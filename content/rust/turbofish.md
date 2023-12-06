---
title: "turbofish syntax"
date: 2023-01-08
template: "page.html"
tags: ["rust/notes"]
---

The turbofish syntax `(::<>)` is used in Rust to specify the type of a generic when calling a function. In Rust, you can define functions that take one or more type parameters, like this:

```rust
fn foo<T>(x: T) -> T {
    x
}
```

The type parameter `T` is a placeholder for a type that will be specified later, when the function is called. When calling this function, you need to specify the type that you want to use for `T`. You can do this in one of two ways:

Infer the type of T by providing an argument of a specific type:

```rust 
let x = foo(5); // T is inferred to be i32
```

Specify the type of `T` explicitly using the turbofish syntax:
```rust 
let x = foo::<i32>(5); // T is explicitly specified as i32
```

The turbofish syntax is useful in cases where the type of the argument is not clear from the context, or when you want to specify the type of `T` explicitly for clarity. It can also be useful when calling functions that have multiple type parameters and you want to specify some but not all of them.
