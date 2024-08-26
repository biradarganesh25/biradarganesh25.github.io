<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Using TLS certificates properly with requests library in Python</title>
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

    <h1> Using TLS certificates properly with requests library in Python </h1>
    <p>Whenever we try to access a "https" website with the requests library, it usually uses openssl toolkit (atleast on linux. not sure about windows) for establishing a secure connection.</p>
<p>The OpenSSL toolkit on linux does not any, by default, have any trusted "root certificates". check <a href="https://support.mozilla.org/en-US/kb/secure-website-certificate">this link</a> for more information on how TLS certificates are validated.</p>
<p>Because of this requests library fails to verify the authenticity of the server and throws an error like this:</p>
<pre><code class="language-text">    certificate verify failed: unable to get local issuer certificate
</code></pre>
<p>To fix this, we'd need to tell openssl where to look for trusted certificates - this is done by CApath argument which specifies the directory containing the trusted certificates. Lets assume the trusted certificates are stored in <code>crts</code> directory (you can get a list of good ones <a href="https://ccadb.my.salesforce-sites.com/mozilla/CACertificatesInFirefoxReport">here</a>).</p>
<p>We can use <code>openssl</code> cli tool to test if TLS verification is working properly. But it expects the names in <code>crts</code> to follow a specific pattern. This can be generated automatically from existing crts:</p>
<pre><code class="language-text">    openssl rehash ./crts
</code></pre>
<p>After this:</p>
<pre><code class="language-text">    openssl s_client -CApath crts -connect hostname:443
</code></pre>
<p>If everything works, you should see something like this:</p>
<pre><code class="language-text">    SSL-Session:
        Protocol  : TLSv1.2
        Cipher    : ECDHE-RSA-AES128-GCM-SHA256
        Session-ID: EB6EF7EBC5A64DA06BF2A073DF528E46B80B7775AC0E58BB07C66B09DF280037
        Session-ID-ctx: 
        Master-Key: 9B83F583A61D7A5F74B3DCD9DABB0414A3E686D98BD297174B189EC57B8123BC221AA37C2ED2DAFD19E5FF6F6F27D468
        PSK identity: None
        PSK identity hint: None
        SRP username: None
        Start Time: 1680743449
        Timeout   : 7200 (sec)
        Verify return code: 0 (ok) #this tells us if verification succeded
        Extended master secret: no
</code></pre>

<footer>
    Made by Ganeshprasad
    </footer>
    </body>
</html>
  