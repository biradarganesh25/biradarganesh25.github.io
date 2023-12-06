---
title: "using certificates properly with requests library in python"
date: "2023-05-04"
author: "ganesh"
tags: ["python","opnenssl"]
---

Whenever we try to access a "https" website with the requests library, it usually uses openssl toolkit (atleast on linux. not sure about windows) for establishing a secure connection.

The OpenSSL toolkit on linux does not any, by default, have any trusted "root certificates". check [this link](https://support.mozilla.org/en-US/kb/secure-website-certificate) for more information on how TLS certificates are validated. 

Because of this requests library fails to verify the authenticity of the server and throws an error like this: 
```
certificate verify failed: unable to get local issuer certificate
```
To fix this, we'd need to tell openssl where to look for trusted certificates - this is done by CApath argument which specifies the directory containing the trusted certificates. Lets assume the trusted certificates are stored in `crts` directory (you can get a list of good ones [here](https://ccadb.my.salesforce-sites.com/mozilla/CACertificatesInFirefoxReport)). 

We can use `openssl` cli tool to test if TLS verification is working properly. But it expects the names in `crts` to follow a specific pattern. This can be generated automatically from existing crts: 

`openssl rehash ./crts`

After this: 

`openssl s_client -CApath crts -connect hostname:443`

If everything works, you should see something like this: 

```
SSL-Session:
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
```

If the certificate validation fails (you can omit the `CApath` argument and try the same command), the output will be something like this: 

```
SSL-Session:
    Protocol  : TLSv1.2
    Cipher    : ECDHE-RSA-AES128-GCM-SHA256
    Session-ID: 2E98282E75BB099F1483C75AE713874E78B0629F8DA052C6D4597AF20E2E0037
    Session-ID-ctx: 
    Master-Key: AFB17089810371B424B25F1353B343C4647242613AE442664641D1AFA448587E95CDAA474F666ECB0DE509553D2ED0B6
    PSK identity: None
    PSK identity hint: None
    SRP username: None
    Start Time: 1680743462
    Timeout   : 7200 (sec)
    Verify return code: 21 (unable to verify the first certificate) #failed!!
    Extended master secret: no
```

Note: Ideally, a server should send all intermediary certificates to the client so that the chain is complete. But many websites do not do this - because of this the crts directory should have intermediate certificates also. This is not a problem when using web-browsers because they automatically download the missing certificates. I did not have time to find if the requests library/openssl cli tool also has this option. 

Now since we verified that certificate chain is being validated properly, we can give the crts directory path to a request session: 

```python
session = requests.session()
session.verify = "./crts"
```


