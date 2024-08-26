--- 
tags: 
    - go 
title: Implementing unbounded nonblocking channels in Go 
--- 

It would have been nice if it was possible to create nonblocking channels in Go with dynamic capacity. At work, I needed a data structure to solve the classic producer/consumer problem - with the following constraints: 

  1. The number of consumers and producers were not known ahead of time
  2. The consumers should stop waiting once the producers are finsihed
  3. The producers should not be blocked if the consumers are not able to keep up 

It the second constraint that made the problem harder - otherwise a simple global buffer protected by locks would've sufficied. 

It is not possible to solve this with channels in Go because to have non-blocking channels you'd need to know the capacity of the channel. So I implemented a data structure which can act as a nonblocking channel with dynamic capacity. This data structure follows some semantics similar to a Go channel:

1. A `Receive` blocks till data is available
2. A close on it will send a signal to all waiting consumers
3. A `Send` on a closed channel will panic

It differs in the following semantics:

1. A `Send` will always suceed - dynamic capacity


The idea is this: have a global buffer that consumers and producers can access, protected by a lock. But we do not use this lock directly - we wrap it in a condition variable. A condition variable provides an additional important functionality necessary to satisfy the second constraint: a way to signal (i.e wake up) consumers waiting (i.e sleeping) on the condition variable.

This signal can be of 2 types:
1. Send the signal to a single waiting consumer
2. Broadcast the signal to all the waiting consumers

A condition variable is used to signal that some condition has been met between threads. It exposes two functionalities: to sleep on the variable and to broadcast on the variable (which wakes up any sleeping threads). 

Condition variables in Go have the both the ability to `Signal` and `Broadcast`.

The idea is that any thread that needs to wait for a condition to be met can sleep on on condition variable. This is much more efficient than continuosly checking it in a for loop. Any other thread that causes this condition to be met can wake up the sleeping threads (if any) using the same condition variable. 

The psuedocode for producer would look like this: 
    
```text
    1. Acquire lock
    2. Add to buffer
    3. If buffer was empty - signal on the condition variable to wake up one sleeping
        (if any) consumers
    4. Release lock
``` 

The psuedocode for consumer would look like: 
    
```text 
    1. Acquire lock via condition variable
    2. if buffer empty:
        wait on condition variable
    3. consume from the buffer
    4. release lock
``` 

This data structure will also provide a `Close` method to `broadcast` to all the sleeping consumers and tell them that no more data will be available. Let's look at the implementation now: 

The Go struct would be: 

```go
type UnboundedChannel[T any] struct {
	buffer      []T
	bufCondVar *sync.Cond
	closed      bool
}
```

The `closed` will be used to check if the channel is closed or not before sending or receiving -
if closed send will panic and receive will return any items remaining in buffer or a zero value.

The actual implementation of the `Send` function (i.e producer)
```go
func (uc *UnboundedChannel[T]) Send(data T) {
	uc.bufCondVar.L.Lock()
	defer uc.bufCondVar.L.Unlock()

	if uc.closed {
		panic("sending on a closed channel")
	}

	uc.buffer = append(uc.buffer, data)
	if len(uc.buffer) == 1 {
		uc.bufCondVar.Signal()
	}

}
```

As in the pseudocode, we first acquire the lock. The case of sending on closed channel was 
not covered in the pseudocode - I wanted to keep that simple and focus on the main concept.
If the buffer was empty, we will `Signal` on the condition variable to wake up one sleeping consumer.

Sending a `Signal` here instead of `Broadcasting` is very important and subtle: in the 
`Receive`, we wait for the condition to be true in a `if`. If producer was `Broadcasting`
instead of `Signalling`, we'd now need to sleep in a `for` loop: because all the waiting 
consumers get awoken at the same time, they cannot be sure that the condition is true

The implementation of `Receive` function (i.e consumer)
```go
func (uc *UnboundedChannel[T]) Receive() (T, bool) {
	uc.bufCondVar.L.Lock()
	defer uc.bufCondVar.L.Unlock()

	if uc.closed {
		var zero T
		return zero, false
	}
	if len(uc.buffer) == 0 {
		uc.bufCondVar.Wait()
		if uc.closed {
			var zero T
			return zero, false
		}
	}

	data := uc.buffer[len(uc.buffer)-1]
	uc.buffer = uc.buffer[:len(uc.buffer)-1]
	return data, true
}
```

The logic here is: after getting the lock, if it has been closed, return a zero value. 
Otherwise, `Wait` for condition to be true: i.e buffer to be not-empty. But when the 
`Receive` gets awoken, it cannot be sure if it is because `Close` was called or `Send` 
was called. Therefore, we again check if `Close` has been called and if it has, we return
the zero value again.

Another thing to note here is that `Receive` returns a boolean which tells whether the data
was returned from the buffer or a zero value was returned. If a zero value was returned, the 
consumers can assume that the channel was closed.

The remaining part is as explained in the pseudocode.

Finally, we can have one more `Close` function, which can be used to tell the consumers that
no more data will be sent:

```go
func (uc *UnboundedChannel[T]) Close() {
	uc.bufCondVar.L.Lock()
	defer uc.bufCondVar.L.Unlock()
	uc.closed = true
	uc.bufCondVar.Broadcast()
}
```

We can panic here if needed - that would maintain similar semantics with a Go channel. 

And that's it! Here's a simple test to make sure it works and show it's usage:

```go
func Test_UnboundedChannel(t *testing.T) {
	uc := NewUnboundedChannel[int]()
	array := make([]int, 10)
	wg := sync.WaitGroup{}

	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			indx, _ := uc.Receive()
			array[indx] = 1
		}()
	}

	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			uc.Send(i)
		}(i)
	}

	wg.Wait()

	for i := 0; i < 10; i++ {
		if array[i] != 1 {
			t.Fatalf("unbounded channel not working")
		}
	}

}
```

This just creates 10 consumers and 10 producers and send a unique value from 
the producers and is verified that all the consumers have all the unique values.

