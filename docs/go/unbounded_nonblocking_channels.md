<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Implementing unbounded nonblocking channels in Go</title>
    <link rel="stylesheet" href="/static/css/style.css" />
    <link rel="stylesheet" href="/static/css/highlighting.css">
    <link rel="stylesheet" href="/static/css/fonts.css" />

  </head>

  <body>
    <nav>
    <ul class="menu">
      <li><a href="/">Home</a></li>
      <li><a href="/tags.html">Tags</a></li>
    </ul>
    <hr/>
    </nav>

    <h1> Implementing unbounded nonblocking channels in Go </h1>
    <p>It would have been nice if it was possible to create nonblocking channels in Go with dynamic capacity. At work, I needed a data structure to solve the classic producer/consumer problem - with the following constraints: </p>
<ol>
<li>The number of consumers and producers were not known ahead of time</li>
<li>The consumers should stop waiting once the producers are finsihed</li>
<li>The producers should not be blocked if the consumers are not able to keep up </li>
</ol>
<p>It the second constraint that made the problem harder - otherwise a simple global buffer protected by locks would've sufficied. </p>
<p>It is not possible to solve this with channels in Go because to have non-blocking channels you'd need to know the capacity of the channel. So I implemented a data structure which can act as a nonblocking channel with dynamic capacity. </p>
<p>The idea is this: have a global buffer that consumers and producers can access, protected by a lock. But we do not use this lock directly - we wrap it in a condition variable. A condition variable provides an additional important functionality necessary to satisfy the second constraint: a way to signal (i.e wake up) consumers waiting (i.e sleeping) on the condition variable. But if the buffer is empty, the producers should wait till it's not - so anytime an element is added to the buffer, if the buffer was empty, we </p>
<p>A condition variable is used to signal that some condition has been met between threads. It exposes two functionalities: to sleep on the variable and to broadcast on the variable (which wakes up any sleeping threads). </p>
<p>The idea is that any thread that needs to wait for a condition to be met can sleep on on condition variable. This is much more efficient than continuosly checking it in a for loop. Any other thread that causes this condition to be met can wake up the sleeping threads (if any) using the same condition variable. </p>
<p>The psuedocode for producer would look like this: </p>
<pre><code class="language-text">    1. Acquire lock
    2. Add to buffer
    3. If buffer was empty - broadcast on the condition variable to wake up any sleeping
        (if any) consumers
    4. Release lock
</code></pre>
<p>The psuedocode for consumer would look like: </p>
<pre><code class="language-text">    1. Acquire lock via condition variable
    2. if buffer empty:
        wait on condition variable
    3. consume from the buffer
    4. release lock
</code></pre>
<p>This data structure will also provide a <code>Close</code> method to <code>broadcast</code> to all the sleeping consumers and tell them that no more data will be available. Let's look at the implementation now: </p>
<p>The Go struct would be: </p>

<footer>
    Made by Ganeshprasad
    </footer>
    </body>
</html>
  