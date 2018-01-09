#!/usr/bin/python
import socket
import select
import time
import argparse


PROTOCOL = {
  'get_relay_port' : '!getrelayport'
}

# Handles one relay client (echo server) socket along with any TCP clients that connect to it
class Relay:
  def __init__(self, relay_socket, host, tcp_port):
    self.relay_socket = relay_socket # Relay client connection
    self.tcp_sockets = [] # List of TCP client connections
    self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Public relay socket
    self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.server_socket.bind((host, tcp_port))
    self.server_socket.listen(5)

    # Handshake with socket server to establish a public relay address
    data = relay_socket.recv(1024)
    if data:
      if data in PROTOCOL.values():
        self._protocol_respond(relay_socket, data)
    
  # Call this method anytime a PROTOCOL value is passed to the relay server
  # (these values tell the relay server to do something other than relay the data)
  def _protocol_respond(self, socket, data):
    if data == PROTOCOL['get_relay_port']:
      port = self.server_socket.getsockname()[1]
      print "Establishing relay address on {0}".format(port)
      socket.send(str(port))

  # Relay data from an input socket to an output socket
  def _relay_data(self, input_socket, output_socket):
    try:
      data = input_socket.recv(1024)
      if data:
        if data in PROTOCOL.values():
          self._protocol_respond(input_socket, data)
        else:
          output_socket.send(data)
          print "Data relayed [{0} -> {1}]:\n\t{2}".format(
            input_socket.getsockname()[1], 
            output_socket.getsockname()[1], 
            data)
    except IOError as e:
      data = None

    return data

  # Check for any new connections, send data from the TCP client to the relay client,
  # from the relay client to the TCP client, and close/remove any sockets that have disconnected
  def do_relay(self, relays):
    # Check for any new TCP client connections
    readable, writable, errored = select.select(
      [self.server_socket] + self.tcp_sockets, 
      [], 
      [], 
      1.0)

    for s in readable:
      if s is self.server_socket:
        # Received new TCP connection
        tcp_socket, address = self.server_socket.accept()
        self.tcp_sockets.append(tcp_socket)
        print "Received connection from {0}".format(tcp_socket.getsockname()[1])
      else:
        # Check for new message from TCP client
        if not self._relay_data(s, self.relay_socket):
          # If _relay_data() returns None the TCP client has disconnected,
          # so close the connection and remove it from the tcp_sockets list
          print "Received disconnect from {0}".format(s.getsockname()[1])
          s.close()
          self.tcp_sockets.remove(s)
        else:
          # Get message back from relay client
          if not self._relay_data(self.relay_socket, s):
            # If _relay_data() returns None the relay client has disconnected,
            # so close the relay client connection and all TCP client connections,
            # then remove the current Relay object from relays[]
            print "Relay address not reachable on {0}".format(self.server_socket.getsockname()[1])
            self.relay_socket.close()
            for tcp_socket in self.tcp_sockets:
              print "Closed connection on {0}".format(tcp_socket.getsockname()[1])
              tcp_socket.close()
            relays.remove(self)


# Parse command line arguments
def get_args():
  parser = argparse.ArgumentParser()
  parser.add_argument("-port", help="port number", type=int)
  parser.add_argument("-host", help="host", default="localhost")

  return parser.parse_args()

def main():
  args = get_args()
  host = args.host
  port = args.port
  relays = []

  # Open a relay server socket for relay clients to connect to
  server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  server_socket.bind((host, port))
  server_socket.listen(5)
  print "Relay server started on {0}:{1}".format(host, port)

  while 1:
    # Check for new relay client connections
    readable, writable, errored = select.select(
      [server_socket], 
      [], 
      [], 
      1.0)

    if len(readable):
      # New relay client has connected, so create a Relay object an begin checking
      # the established port for new TCP connections
      port += 1
      relay_socket, address = server_socket.accept()
      relays.append(Relay(relay_socket, host, port))
      
    for relay in relays:
      # Loop through each relay client and relay messages for each connected TCP client
      # (if a relay client disconnects, it will remove itself from the relays list)
      relay.do_relay(relays)


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    pass