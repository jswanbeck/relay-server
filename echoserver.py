#!/usr/bin/python
import socket
import argparse
from relay import PROTOCOL


def get_args():
  parser = argparse.ArgumentParser()
  parser.add_argument("-relay", help="address of relay server")

  return parser.parse_args()

def main():
  args = get_args()
  host, port = args.relay.split(':')

  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect((host, int(port)))

  s.send(PROTOCOL['get_relay_port'])
  public_relay_port = s.recv(1024)
  print "Connection established on {0}".format(public_relay_port)

  while True:
    data = s.recv(1024)
    s.send(data)


if __name__ == "__main__":
  try:
    main()
  except KeyboardInterrupt:
    pass
