[ ] _packet_queue.wait_for(picker,timeout) method to block until specific packet
    arrives.

[ ] add another event _packet_queue._specific_pack for the arrival of the
    specific packet.

[ ] add _packet_queue._wait_picker defaulting to lambda p: True; for setting
    specific_pack event.

[ ] redesign  _packet_queue.pick. Add wait_for parameter.

[ ] redesign fvwmpy.get* methods employing pakets.wait_for method.

[ ] redesign fvwmpy.{var,infostore} employing pakets.wait_for method.

[ ] reflect changes in README.md