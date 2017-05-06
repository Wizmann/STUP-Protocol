#coding=utf-8
from twisted.internet import defer
from twisted.internet import task
from twisted.internet import protocol
from twisted.internet import reactor

import copy
import logging
import traceback

from .. import Config
from .. import StupPacket
from .. import Utils
from .. import StateMachine
from .. import TwistedUtils
from ..RingContainer import RingBuffer, RingWindow, ContainerItem
from ..TwistedUtils import DeferredDeque

class StupCore(object):
    class PacketItem(object):
        def __init__(self, packet, retry):
            self.packet = packet
            self.retry = retry

    def __init__(self, protocol):
        self.NAGLE_TIMEOUT = Utils.millisecond_to_second(Config.NAGLE_DELAY)
        self.SEND_CHUNK_SIZE = Config.CHUNK_SIZE
        self.RETRY_THRESHOLD = Config.RETRY_THRESHOLD
        self.WAIT_ALL_DONE_TIMEOUT = Utils.millisecond_to_second(Config.WAIT_ALL_DONE_TIMEOUT)
        self.FAST_RESEND_THRESHOLD = Config.FAST_RESEND_THRESHOLD

        self.protocol = protocol
        self.reactor = reactor

        self.recv_seq_id = -1
        self.send_seq_id = Utils.to_u32(
                Utils.rand_u32() + Utils.cur_millisecond() / 500 * 64000)

        self.fin_wait = Utils.to_u32(Config.FIN_WAIT)

        self.input_window = None
        self.output_buffer = RingBuffer(
                Config.SEND_BUFFER_SIZE, self.send_seq_id)

        self.nagle_next = 0
        self.nagle_buffer = ''

        self.send_q = DeferredDeque()
        self.send_q.pop_left().addCallback(self._send_packet)

        self.fin_sent = False

        self.sending_table = set()

        self.last_ack_id = self.next_ack_id()

        self.last_recv_ack_id = -1
        self.last_recv_ack_cnt = 0

        self.time_wheel_fine   = TwistedUtils.TimeWheel(255, Config.TIMER_FINE_GRANULARITY)
        self.time_wheel_coarse = TwistedUtils.TimeWheel(10, Config.TIMER_COARSE_GRANULARITY)
        self.tick_fine()
        self.tick_coarse()

        self.rtt_estimator = Utils.TcpRttEstimator()
        self.liv_rtts = {}
        self.rtt = Config.RTT_DFT

    def tick_fine(self):
        self.time_wheel_fine.moveNext()
        self.tick_fine_d = task.deferLater(
            self.reactor, Config.TIMER_FINE_GRANULARITY, self.tick_fine)
        self.tick_fine_d.addBoth(Utils.nop)

    def tick_coarse(self):
        self.time_wheel_coarse.moveNext()
        self.tick_coarse_d = task.deferLater(
            self.reactor, Config.TIMER_COARSE_GRANULARITY, self.tick_coarse)
        self.tick_coarse_d.addBoth(Utils.nop)

    @property
    def state_machine(self):
        return self.protocol.state_machine

    @property
    def state(self):
        return self.state_machine.state

    @property
    def peer_addr(self):
        return self.protocol.peer_addr

    def is_idle(self):
        return self.time_wheel_fine.isEmpty() and \
            not self.send_q.pending

    def set_state(self, state_nr):
        logging.debug("set state: %d" % state_nr)
        self.state_machine.set_state(state_nr)

    def callLater(self, time, cb, *args, **kwargs):
        if time <= self.time_wheel_fine.maxTimeout():
            self.time_wheel_fine.addCallLater(time, cb, *args, **kwargs)
        elif time <= self.time_wheel_coarse.maxTimeout():
            self.time_wheel_coarse.addCallLater(time, cb, *args, **kwargs)
        else:
            logging.error("error on callLater [%d|%s]" % (time, cb))

    def reset(self):
        self.time_wheel_fine.clear()
        self.time_wheel_coarse.clear()

        for d in self.get_all_defers():
            d.cancel()

        if self.state.state_nr == StateMachine.RST:
            return
        self.state_machine.set_state(StateMachine.RST)
        for i in xrange(Config.RST_SEND_TIMES):
            self.send_ctrl_packet(StupPacket.RstPacket())
        self.handle_rst()

    def handle_rst(self):
        self.time_wheel_fine.clear()
        self.time_wheel_coarse.clear()
        self.state_machine.set_state(StateMachine.RST)

        logging.debug('start cleanup')
        for d in self.get_all_defers():
            d.cancel()

        # it just a ... lying to yourself, actually this
        # cleaning process doesn't make any sence at all
        self.send_q.pending.clear()
        self.sending_table = set()

        self.protocol.cleanUp()

    def finalize(self):
        self.fin_sent = True
        self.send('', fin=1, psh=1)

    def handle_fin(self):
        if self.fin_sent:
            for i in xrange(Config.FIN_ACK_SEND_TIMES):
                self.send('', ack=1, psh=1)
        else:
            self.send('', fin=1, ack=1, psh=1)
            self.fin_sent = True
            self.state_machine.set_state(StateMachine.FIN)

        self.recv = Utils.nop
        self.callLater(self.fin_wait, self._handle_fin)

    def _handle_fin(self):
        self.time_wheel_fine.clear()
        self.time_wheel_coarse.clear()
        self.tick_fine_d.cancel()
        self.tick_coarse_d.cancel()
        for d in self.get_all_defers():
            d.cancel()

        logging.debug('start cleanup')
        self.protocol.cleanUp()

    def is_all_done(self):
        return not self.sending_table

    @defer.inlineCallbacks
    def wait_all_done(self):
        while not self.is_all_done() or not self.is_idle():
            logging.debug("waiting for all process to be done")
            yield TwistedUtils.sleep(self.WAIT_ALL_DONE_TIMEOUT)

    def connection_made(self):
        self.callLater(5, self.rtt_detect)

    def rtt_detect(self):
        seq_number = Utils.to_u32(self.output_buffer.range_l - 1)
        liv_packet = StupPacket.LivPacket(seq_number)
        self.send_ctrl_packet(liv_packet)
        self.liv_rtts[seq_number] = Utils.cur_second()

        self.callLater(5, self.rtt_detect)
        self.callLater(5 * 60, self.liv_timeout, seq_number)

    def liv_timeout(self, seq_number):
        if seq_number in self.liv_rtts:
            self.reset()

    def build_connection(self, packet):
        # recv client syn packet
        if packet.syn and not packet.ack:
            self.input_window = RingWindow(Config.RECV_WINDOW_SIZE, packet.seq_number)
            self.input_window.add(
                    ContainerItem(packet.seq_number, packet.seq_number + 1, packet))
            self.input_window.pop_left_until(lambda x: False)

            self.send('', syn=1, ack=1, psh=1)
            self.set_state(StateMachine.LISTEN)
        elif packet.syn and packet.ack:
            if self.output_buffer.range_r != packet.ack_number:
                logging.debug("invalid syn ack packet received, ignore it")
                return ''

            syn_pack = self.output_buffer.pop_left_until(lambda x: False)
            if len(syn_pack) != 1:
                #self.reset()
                return ''

            logging.debug("pop out sent syn: %s" % str(syn_pack[0].payload.packet))

            self.input_window = RingWindow(Config.RECV_WINDOW_SIZE, packet.seq_number)
            self.input_window.add(
                    ContainerItem(packet.seq_number, packet.seq_number + 1, packet))
            self.input_window.pop_left_until(lambda x: False)

            self.send('', ack=1, psh=1)
            self.set_state(StateMachine.ESTABLISHED)
            self.connection_made()
            self.protocol.connectionMade()

        return ''

    def fast_resend(self, ack_id):
        if ack_id != self.last_recv_ack_id:
            self.last_recv_ack_id = ack_id
            self.last_recv_ack_cnt = 1
        else:
            self.last_recv_ack_cnt += 1

        if self.last_recv_ack_cnt >= self.FAST_RESEND_THRESHOLD \
                and self.last_recv_ack_cnt % self.FAST_RESEND_THRESHOLD == 0:
            item = self.output_buffer.get(ack_id)
            if not item:
                return
            self.send_packet_fast(item.payload.packet)

    def recv(self, packet):
        if not self.input_window:
            return self.build_connection(packet)

        if packet.ack:
            ack_id = packet.ack_number
            if self.output_buffer.contains(ack_id) or ack_id == self.output_buffer.range_r:
                if self.state.state_nr == StateMachine.LISTEN:
                    self.set_state(StateMachine.ESTABLISHED)
                    self.connection_made()
                    self.protocol.connectionMade()
                popped_packets = self.output_buffer.pop_left_until(lambda x: x.range_l == ack_id)

                self.fast_resend(ack_id)
            elif packet.liv and ack_id in self.liv_rtts:
                delta = Utils.cur_second() - self.liv_rtts[ack_id]
                self.rtt = self.rtt_estimator.nextRTO(delta)
                logging.debug("estimated rtt[%s]: %f | %f", self.peer_addr, delta, self.rtt)
                self.liv_rtts = {}
            elif packet.liv:
                logging.error("outside-window liv ack, just ignore")
            else:
                logging.debug("outside-window ack, just ignore")

        if packet.data or packet.syn or packet.fin or packet.liv:
            seq_id = packet.seq_number
            if not self.input_window.contains(seq_id):
                logging.debug('recv out-of-window packet, send ack to sync')
                if packet.liv and not packet.ack:
                    livack_packet = StupPacket.LivAckPacket(seq_id)
                    self.send_ctrl_packet(livack_packet)
                else:
                    self.send('', ack=1)
            else:
                l = seq_id
                r = Utils.seq_add(
                        seq_id, len(packet.data) + (1 if (packet.syn or packet.fin) else 0))
                self.input_window.add(ContainerItem(l, r, packet))

        avail_data = self.input_window.pop_left_to(lambda item: item.payload.fin)
        if avail_data:
            data = ''.join(map(lambda pack: pack.payload.data, avail_data))
            if avail_data[-1].payload.fin:
                self.handle_fin()
            elif data:
                self.send('', ack=1)
            return data
        return ''

    def nagle_refrsh(self):
        self.nagle_next = Utils.cur_second() + self.NAGLE_TIMEOUT
        self.callLater(
                self.NAGLE_TIMEOUT, self._send, '', **{'nagle_psh': 1})

    def has_packet_to_send(self):
        return self.last_ack_id != self.next_ack_id() or self.nagle_buffer

    def is_sending(self, seq_number):
        return seq_number in self.sending_table

    def send(self, msg, **kwargs):
        if len(msg) + self.output_buffer.size() > self.output_buffer.capacity():
            logging.debug("Output buffer is full!")
            return -1

        syn = kwargs.get('syn', 0)
        fin = kwargs.get('fin', 0)
        is_send = self._send(msg, **kwargs)

        if is_send:
            #logging.debug("msg[%s] sent, nagle timer refreshed %f" % (str(kwargs), self.NAGLE_TIMEOUT))
            pass
        elif self.has_packet_to_send() and Utils.cur_second() >= self.nagle_next:
            #logging.debug("msg[%s] not sent, but nagle timer refreshed %f" % (str(kwargs), self.NAGLE_TIMEOUT))
            self.nagle_refrsh()
        else:
            #logging.debug("msg[%d][%s] not sent" % (len(msg), str(kwargs)))
            pass

        return len(msg) + (1 if (syn or fin) else 0)

    def _send(self, msg, **kwargs):
        syn = kwargs.get('syn', 0)
        psh = kwargs.get('psh', 0)
        fin = kwargs.get('fin', 0)
        nagle_psh = kwargs.get('nagle_psh', 0)

        if syn or psh or fin:
            if self.nagle_buffer:
                self.send_msg(self.nagle_buffer)
            self.send_msg(msg, **kwargs)
            if self.state.state_nr == StateMachine.CLOSED and syn:
                self.set_state(StateMachine.LISTEN)
            return True

        self.nagle_buffer += msg

        if len(self.nagle_buffer) >= self.SEND_CHUNK_SIZE:
            chunk_remain = len(self.nagle_buffer) % self.SEND_CHUNK_SIZE
            chunk_send = len(self.nagle_buffer) - chunk_remain

            buffer_to_send = self.nagle_buffer[:chunk_send]
            self.nagle_buffer = self.nagle_buffer[chunk_send:]

            self.send_msg(buffer_to_send)
            return True
        elif (nagle_psh or self.is_idle()) and self.has_packet_to_send():
            buffer_to_send, self.nagle_buffer = self.nagle_buffer, ''
            self.send_msg(buffer_to_send)
            return True

        return False

    def send_msg(self, msg, **kwargs):
        syn = kwargs.get('syn', 0)
        fin = kwargs.get('fin', 0)
        psh = kwargs.get('psh', 0)

        if not msg and not syn and not fin:
            packet = StupPacket.Packet()
            packet.ack = 1
            packet.psh = psh
            packet.ack_number = self.next_ack_id()
            self.last_ack_id = packet.ack_number
            self.send_ctrl_packet(packet)
            return

        pack_size = len(msg) + (1 if (syn or fin) else 0)

        chunk_num = (pack_size + self.SEND_CHUNK_SIZE - 1) / self.SEND_CHUNK_SIZE
        for chunk_idx in xrange(chunk_num):
            chunk = msg[chunk_idx * self.SEND_CHUNK_SIZE: (chunk_idx + 1) * self.SEND_CHUNK_SIZE]

            l = self.send_seq_id
            r = self.send_seq_id + len(chunk) + (1 if (syn or fin) else 0)

            self.send_seq_id = r

            packet = StupPacket.Packet(chunk)
            packet.seq_number = l
            packet.syn = syn
            packet.psh = psh

            if chunk_idx == chunk_num - 1 and fin:
                packet.fin = 1

            packet_item = self.PacketItem(packet, 0)
            self.output_buffer.append(ContainerItem(l, r, packet_item))
            self.send_packet(packet)

    def send_packet(self, packet):
        self.sending_table.add(packet.seq_number)
        self.send_q.append_right(packet)

    def send_packet_fast(self, packet):
        urg_packet = copy.copy(packet)
        urg_packet.urg = 1
        self.send_q.append_left(urg_packet)

    def _send_packet(self, cur_packet):
        eta = 0
        packet_to_send = []
        if cur_packet:
            packet_to_send.append(cur_packet)

        while eta <= Config.TIMER_FINE_GRANULARITY * 3 and self.send_q.pending:
            packet = self.send_q.pending.popleft()
            if self.output_buffer.contains(packet.seq_number):
                packet_to_send.append(packet)
                eta += self.calc_eta(packet.size())

        if not packet_to_send:
            self.send_q.pop_left().addCallback(self._send_packet)
            return

        if self.last_ack_id != self.next_ack_id():
            packet = packet_to_send[-1]
            packet.ack = 1
            self.last_ack_id = self.next_ack_id()
            packet.ack_number = self.last_ack_id

        for packet in packet_to_send:
            if not packet.urg and self.is_sending(packet.seq_number):
                self.sending_table.remove(packet.seq_number)

            packet_buf = packet.pack()
            self.protocol.transport.write(packet_buf, self.peer_addr)

            if not packet.urg:
                self.schedule_retry(packet)

        self.callLater(Config.TIMER_FINE_GRANULARITY, 
                self.send_q.pop_left().addCallback,
                self._send_packet)

        self.nagle_refrsh()

    def schedule_retry(self, packet):
        seq_number = packet.seq_number
        item = self.output_buffer.get(seq_number)
        if not item:
            return

        item.payload.retry += 1
        if item.payload.retry >= self.RETRY_THRESHOLD:
            if self.state.state_nr != StateMachine.RST:
                self.reset()
            return
        self.callLater(self.get_timeout(item.payload.retry), self.resend_packet, packet)

    def resend_packet(self, packet):
        is_sending = self.is_sending(packet.seq_number)
        is_not_sent = self.output_buffer.get(packet.seq_number)
        if not is_sending and is_not_sent:
            self.send_packet(packet)

    def get_timeout(self, retry):
        timeout = self.rtt * (1 << (retry - 1))
        timeout = min(5, timeout)
        timeout = max(0.1, timeout)
        return timeout

    def get_all_defers(self):
        return [self.tick_fine_d, self.tick_coarse_d]

    def cancel_all_defers(self):
        for d in self.get_all_defers():
            d.cancel()

    def send_ctrl_packet(self, packet):
        packet_buf = packet.pack()
        self.protocol.transport.write(packet_buf, self.peer_addr)

    def calc_eta(self, size):
        return max(0, 1.0 * size / Config.BANDWIDTH)

    def next_ack_id(self):
        if not self.input_window:
            return -1
        return self.input_window.range_l
