--- 
tags: 
    - pluscal 
    - formal-verification
title: Learning formal verification by writing a spec for verifying a zero-downtime database migration in PlusCal
published_date: "2024-12-28"
--- 

Formal verification can be used to analyze complex systems to ensure 
their correctness. Formal verification is the process of checking that a system 
satisfies specific properties (which are specified by the user) across all possible states. 
There are 2 main types of properties: 
"safety properties" and "liveness properties". For the formal definition,
please [refer here](https://will62794.github.io/formal-methods/2020/08/01/safety-and-liveness.html).
If a property is not satisfied in any state but has the potential to be
satisfied in a future state, then that would be a "liveness 
property". If it can never be satsified in any future state, then it would
be a "safety property".

For example, let's imagine a bunch of servers serving a website. A property
saying that "no server can ever be offline" would be a safety property 
because if in any state of the system, any server goes offline the property
would not be satisfied and can never be satisfied in any future state 
after that. But a property saying that "all servers that go offline
eventually come back online" would be a "liveness property" because 
there is always a possiblity of that being true in a future state.

TLA+ is a formal specification language where we can model systems 
and verify properties across all possible system states. It 
allows us to enumerate all possible states a system can be 
in and verify that specified properties hold true 
across all these states.

PlusCal is a DSL for TLA+. It sits at a higher level of abstraction
and is much easier to specify complex systems in it compared to TLA+.
The trade-off is that some kinds of systems cannot be specified (i.e
it is more constrained than TLA+, but it is sufficient for most 
common use cases). 

I went through [learn tla](https://learntla.com/index.html) in about 2 weeks (it 
was quite dense - I ended up learning some things about formal verification in order
to understand that material fully). I thought that the best way to learn it would be 
to write a spec that actually does something useful and I thought verifying a zero-
downtime database migration algorithm would be fun.

Let's assume a service exposes 3 APIs: `Upsert` either updates or creates a new object
, `Delete` which deletes the object and `Get` which gets the object. 
We want to migrate these objects (for simplicity 
purposes let's assume its a table in a SQL database) from one database (`olddb`) 
to another (`newdb`). 

The pseudocode for migration algorithm is as follows:

Note: the pseudocode assumes that the database is a mapping of 
primary keys to values (the objects in question are assumed to
have a primary key and a value)

The `Upsert` operation:

```text
Upsert(key, val) {
    newdb[key] = val
}
```

```text
Delete(key, val) {
  // we need to put a TOMBSTONE instead of actually
  // deleting it so that the background migration
  // process does not accidentally insert a 
  // deleted value
  newdb[key] = TOMBSTONE
}
```

```text
Get(key) {
    if key in newdb {
        val = newdb[key]
        if val == TOMBSTONE {
            return NULL
        } else {
            return val
        }
    } else if key in olddb {
        return olddb[key]
    }
    return NULL
}
```

And a background migration process that moves all the objects from
`olddb` to `newdb`

```text
migrate() {
  for key, val in olddb {

    // if does not exist is a conditional insert 
    newdb[key] = val if does not exist
  }
}
```

This is the pluscal spec for the above migration algo:

```text
---- MODULE test ----
EXTENDS Integers, FiniteSets, TLC

Threads == {1,2} \* each thread represents a user
N == 1..4 \* primary keys of objects that user will use
Objects ==  [p \in N |-> p] \* the values that primary keys map to 

CONSTANTS 
    NULL,
    TOMBSTONE
    
(* --algorithm zero_downtime_migration

variables 
\* db is used to simulate a system without migration. 
\* olddb and newdb are used to simulate system with migration

db = [pkey \in 1..2 |-> pkey+1], \* some objects will already exist in db with different values when migration starts
olddb = [pkey \in 1..2 |-> pkey+1],
newdb = [pkey \in {} |-> NULL],

define 
  TypeOK == 
       \/ DOMAIN db \subseteq DOMAIN Objects
       \/ Cardinality(DOMAIN db) = 0
      
  GetObjectWOMigration(pkey) == 
    IF pkey \in DOMAIN db
    THEN db[pkey]
    ELSE NULL
        
  GetObjectWMigration(pkey) == 
    IF pkey \in DOMAIN newdb 
    THEN IF newdb[pkey] = TOMBSTONE 
         THEN NULL
         ELSE newdb[pkey]
    ELSE IF pkey \in DOMAIN olddb 
         THEN olddb[pkey]
         ELSE NULL
    
 \* the system with migration and without migration will be compared 
 \* this is our main invariant - we mimick a system where there is no 
 \* migration happening so that we can use that to check that our system
 \* where the migration is happening is correct
  ConsistentViews ==
    /\ \A pkey \in N: GetObjectWOMigration(pkey) = GetObjectWMigration(pkey)
    
end define;

\* WOMigration represent operations for the system without migration
\* WMigration represents operations for system with migration

macro UpsertWOMigration(db, key, val) begin
        db := (key :> val) @@ db;
end macro;

macro DeleteWOMigration(db, key) begin
  if key \in DOMAIN db then
    db := [p \in DOMAIN db \ {key} |-> db[p]]
  end if;
end macro;

macro UpsertWMigration(newdb, key, val) begin
        newdb := (key :> val) @@ newdb;
end macro;

macro DeleteWMigration(newdb, key) begin
  newdb := (key :> TOMBSTONE) @@ newdb
end macro;

\* each process represents 1 user
\* each will randomly pick an object and either upsert or delete it
process thread \in Threads
  
  variables
  i = 0,
  curPkey = NULL;
  
  begin
    Start:
      while i < 2 do
        PickObject:
          with pkey \in N do
            curPkey := pkey;
          end with;
        ChooseOperation:
          either 
            goto Upsert;
          or
            goto Delete;
          end either;
        Upsert:
          either
          \* we perform the same operation in the with and without migration system atomically
          \* at the end of each operation, both the systems should return the same values for all the objects
            UpsertWOMigration(db, curPkey, Objects[curPkey]);
            UpsertWMigration(newdb, curPkey, Objects[curPkey]);
            goto IncCounter;
          or 
          \* represents error - i.e 5xx to user. we need to error out in both the systems.
            goto IncCounter;
          end either;
        Delete:
         either
            DeleteWOMigration(db, curPkey);
            DeleteWMigration(newdb, curPkey);
            goto IncCounter;
         or
            goto IncCounter;
          end either;
        IncCounter:
          i := i + 1;
     end while;
        
  end process;

\* this is the background migration process that copies over values from oldb to newdb
process bg_migration = 3

  variables
  existingPkeys = DOMAIN olddb,
  curPkey = NULL,
  
  begin
    Start:
      while existingPkeys /= {} do 
        Pick:
          with pkey \in existingPkeys do
            curPkey := pkey;
            existingPkeys := existingPkeys \ {curPkey};
          end with;
        Migrate:
        \* *note*: this entire get and set is atomic (i.e create if not exist). 
        \* if you make the get and set non-atomic, the spec will fail (as it should)
          if curPkey \notin DOMAIN newdb
          then
            newdb := (curPkey :> olddb[curPkey]) @@ newdb;
          end if;          
      end while;
          
end process;

end algorithm; *)
```

Its amazing how the main part of the spec looks very similar to the pseudocode. 

The trickiest thing was to figure out the invariant - i.e how to make sure that our 
migration algorithm was correct. For this, I simulate 2 services in the spec: one 
where the migration is happening and another where it is not. And our invariant will 
be that `GET` operations on all the objects give the exact same value in both the 
services. 


Lets define the main variables involved: 

`Objects` represents the objects that the users will work with. This is a function 
that maps primary keys of the objects to their values. Each object is 
assumed to have a primary key and a value. The spec uses 4 objects. 
`db` is the database used by the service without migration. `olddb` and `newdb` are 
are databases used by the service with migration. All the database variables are 
functions mapping primary keys of objects to values.

All the service APIs are written as macros. 
The APIs for service with migration end with `WMigration`
and for the service without migration end with `WOMigration`

Note: the database updates are
implemented as function updates in pluscal - and the database shows up on the right.
This is because the operator `@@` merges the keys in the 
`left_function @@ right_function`
and uses the value of the key in the `left_function` if present in both the functions.
The `GET` operation is implemented as an operator - because macros in pluscal do not 
return values.

One thing I realized is that there is a lot of freedom in modelling complex systems in 
TLA+. This lets us represent complex interactions in a very simple manner (for e.g 
a database insert operation as a function update). This freedom might seem a bit weird
when just starting with plucal/tla+, but its very powerful once we get used to it. 

Let's talk about the processses involved in the spec now. 

The spec has simulates 2 users randomly picking pre-defined objects (4 objects) and 
then randomly 
performing either `Upsert` or `Delete` operations on them. 
Each user does this 2 times. The database starts out 
with some objects already present (2 objects). The objects that the users pick and 
perform operations on will include these already present 
objects also. The number of users and objects and the number of times an action is repeated
might
seem very few to test with to make sure that the system is working properly, but since 
the TLC model checker will create a state graph which includes every possible state, we 
can be sure that all the edge cases are covered.
All actions happening in our system with migration will be mirrored in a system without
migration atomically.

There is also a background migration process running which copies over the data from
`olddb` to `newdb`.

The final migration step involves deleting the `TOMBSTONES` in the newdb, but for now
the spec does not have it. In future I might add it and revise this blog post.

The true value of TLA+ spec shows up when the spec errors out. For example, when writing
the spec I had written the `GetObjectWMigration` incorrectly: 

```text
GetObjectWMigration(pkey) == 
    IF pkey \in DOMAIN newdb 
    THEN newdb[pkey]
    ELSE IF pkey \in DOMAIN olddb 
         THEN olddb[pkey]
         ELSE NULL
```

compare this to the correct version:

```text
GetObjectWMigration(pkey) == 
  IF pkey \in DOMAIN newdb 
  THEN IF newdb[pkey] = TOMBSTONE 
        THEN NULL
        ELSE newdb[pkey]
  ELSE IF pkey \in DOMAIN olddb 
        THEN olddb[pkey]
        ELSE NULL
```

The incorrect version does not handle the case where there is a `TOMBSTONE` present in newdb. 
Because of this the spec was failing. 

This is a solid example of how TLA+ saves time: it lets us discover desgin flaws very early. 
Imagine debugging this error after writing out the entire migraiton algorithm: it would've 
hard to do and a very real chance that it'd have been missed altogether. Here, I just had to 
step through the state changes to figure out the exact cause of the spec failure.

One more way in which TLA+ helps is it forces us to think which steps must be atomic. If we 
come across any steps that cannot be atomic then it forces to consider the implications of 
concurrent execution. For example, in the background migration process above, before moving
an item from `olddb` to `newdb` we check if the object already exists in the `newdb` (this
maybe because it was deleted. If it was, we should not overwrite the `TOMBSTONE`). Checking 
whether the object exists and creating it in the `newdb` must be atomic (most databases have 
a `IF DOES NOT EXIST` support for conditional statements). While this may seem trivial, when
writing the TLA+ spec it made it very clear and bought it to the focus. Important information
like this when discovered early in the design phase can save a lot of time during implementation
(for e.g here we would need to make sure that `newdb` has support for conditional statements 
when choosing the database)  



