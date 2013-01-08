from __future__ import absolute_import

import time
import bisect
import select
from threading import Thread

from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api
from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp


class Instr(object):
    """Abstract MIB instruction."""

    @property
    def name(self):
        raise NotImplementedError()

    def __cmp__(self, other):
        return cmp(self.name, other)

    def execute(self, module, *args, **kwargs):
        raise NotImplementedError()

    def __call__(self, protoVer, *args, **kwargs):
        return self.execute(api.protoModules[protoVer], *args, **kwargs)


class SysDescr(Instr):

    name = (1, 3, 6, 1, 2, 1, 1, 1, 0)

    def execute(self, module):
        return module.OctetString(
            'PySNMP example command responder at %s' % __file__
        )


class Uptime(Instr):

    name = (1, 3, 6, 1, 2, 1, 1, 3, 0)
    birthday = time.time()

    def execute(self, module):
        return module.TimeTicks(
            (time.time() - self.birthday) * 100
        )


class Agent(object):

    def __init__(self, host, port):
        self._mibInstr = []
        self._mibInstrIdx = {}
        self._transportDispatcher = AsynsockDispatcher()
        self.host = host
        self.port = port

    def prepare(self):
        address = (self.host, self.port)
        transportDispatcher = self._transportDispatcher
        transportDispatcher.registerTransport(
            udp.domainName, udp.UdpSocketTransport().openServerMode(address)
        )
        transportDispatcher.registerRecvCbFun(self.cbFun)
        transportDispatcher.jobStarted(1)

    def start(self):
        try:
            self._transportDispatcher.runDispatcher()
        except select.error:
            pass

    def stop(self):
        self._transportDispatcher.closeDispatcher()

    def registerInstr(self, instr):
        assert callable(instr)
        self._mibInstr.append(instr)
        self._mibInstrIdx[instr.name] = instr

    def cbFun(self, transportDispatcher, transportDomain, transportAddress, wholeMsg):
        mibInstr = self._mibInstr
        mibInstrIdx = self._mibInstrIdx
        while wholeMsg:
            msgVer = api.decodeMessageVersion(wholeMsg)
            if msgVer in api.protoModules:
                pMod = api.protoModules[msgVer]
            else:
                return
            reqMsg, wholeMsg = decoder.decode(
                wholeMsg, asn1Spec=pMod.Message(),
                )
            rspMsg = pMod.apiMessage.getResponse(reqMsg)
            rspPDU = pMod.apiMessage.getPDU(rspMsg)
            reqPDU = pMod.apiMessage.getPDU(reqMsg)
            varBinds = []
            errorIndex = -1
            # GETNEXT PDU
            if reqPDU.isSameTypeWith(pMod.GetNextRequestPDU()):
                # Produce response var-binds
                errorIndex = -1
                for oid, val in pMod.apiPDU.getVarBinds(reqPDU):
                    errorIndex = errorIndex + 1
                    # Search next OID to report
                    nextIdx = bisect.bisect(mibInstr, oid)
                    if nextIdx == len(mibInstr):
                        # Out of MIB
                        pMod.apiPDU.setEndOfMibError(rspPDU, errorIndex)
                    else:
                        # Report value if OID is found
                        varBinds.append(
                            (mibInstr[nextIdx].name, mibInstr[nextIdx](msgVer))
                        )
            elif reqPDU.isSameTypeWith(pMod.GetRequestPDU()):
                for oid, val in pMod.apiPDU.getVarBinds(reqPDU):
                    if oid in mibInstrIdx:
                        varBinds.append(
                            (oid, mibInstrIdx[oid](msgVer))
                        )
                    else:
                        # No such instance
                        try:
                            pMod.apiPDU.setNoSuchInstanceError(rspPDU, errorIndex)
                        except IndexError:
                            pass
                        varBinds = pMod.apiPDU.getVarBinds(reqPDU)
                        break
            else:
                # Report unsupported request type
                pMod.apiPDU.setErrorStatus(rspPDU, 'genErr')
            pMod.apiPDU.setVarBinds(rspPDU, varBinds)
            transportDispatcher.sendMessage(
                encoder.encode(rspMsg), transportDomain, transportAddress
            )
        return wholeMsg


class BackgroundAgent(Agent):

    Container = Thread

    def __init__(self, host, port):
        super(BackgroundAgent, self).__init__(host, port)
        self.container = None

    def start(self):
        assert self.container is None
        self.prepare()
        container = self.container = self.Container(
            target=super(BackgroundAgent, self).start
        )
        container.daemon = True
        container.start()

    def stop(self):
        assert self.container is not None
        super(BackgroundAgent, self).stop()
        self.container.join()
        self.container = None
