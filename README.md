# relay-server
A generic TCP relay

The relay server (relay.py) is designed to connect to accept connections from relay clients and TCP clients -- for a proof of concept the relay clients will be echo servers which receive some data from the relay server and send it right back. 

TCP clients (e.g. telnet) will interface with the echo servers by connecting to the relay server via a publicly accessible port (provided to the echo server when it first connects to the relay), then sending data which will be relayed from the relay server to the echo server and back to the relay server and finally the TCP client.

The relay server accepts the argument "port" and the echo server accepts the argument "relay" as shown in this example workflow:

```
$ ./relay -port 8000
> Relay server started on localhost:8000

$ ./echoserver -relay localhost:8000
> Connection established on 8001

$ telnet localhost 8001
hello world!
> hello world!
```

There can be multiple echo servers running at once, and multiple TCP clients connected to each echo server.
