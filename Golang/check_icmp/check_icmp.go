package main

/*

  ________   _______  ________  _________  _______   ________
  |\_____  \ /  ___  \|\   __  \|\___   ___\\  ___ \ |\   ____\
  \|___/  //__/|_/  /\ \  \|\  \|___ \  \_\ \   __/|\ \  \___|
      /  / /__|//  / /\ \  \\\  \   \ \  \ \ \  \_|/_\ \  \
     /  / /    /  /_/__\ \  \\\  \   \ \  \ \ \  \_|\ \ \  \____
    /__/ /    |\________\ \_______\   \ \__\ \ \_______\ \_______\
    |__|/      \|_______|\|_______|    \|__|  \|_______|\|_______|

    http://www.720tec.es
    Borja Blasco García <bblasco@720tec.es>
    Check icmp
    Version 1.0

 NOTE: When a threshold is set, both levels, critical and warning, h

 USAGE: checkSize -path <path_to_file> -file <file> [-w <size>[k|m|g]] [-c <size>[k|m|g]] [-name <service_name>]
 Default size by Bytes
*/

import (
	"flag"
	"fmt"
	"net"
	"os"
	"time"

	"github.com/tatsushid/go-fastping"
)

type CheckStatus struct {
	code       int
	message    string
	ip         string
	packets    int
	time       float64
	pktpercent float64
	wtime      float64
	wpacket    float64
	ctime      float64
	cpacket    float64
	threshold  bool
}

const (
	OK   = 0
	WARN = 1
	CRIT = 2
	UNK  = 3
)

var status CheckStatus

func main() {
	ip := flag.String("ip", "", "IP to ping")
	packets := flag.Int("packet", 4, "Packets to send")
	wtime := flag.Float64("wrtt", 0.0, "Response time for warning")
	ctime := flag.Float64("crtt", 0.0, "Response time for critical")
	wpkt := flag.Float64("wpl", 0.0, "Percent of packets lost for warning")
	cpkt := flag.Float64("cpl", 0.0, "Percent of packets lost for critical")

	flag.Parse()

	if *ip == "" {
		error(3, "USAGE: check_icmp -ip <Remote_IP> [-packet <number_packets>] [-wrtt <time_warn>] [-wpt <packet_warn>] [-crtt <time_crit>] [-cpl <packet_crit>]")
		return
	}

	status.ip = *ip
	status.packets = *packets
	status.wtime = *wtime
	status.wpacket = *wpkt
	status.ctime = *ctime
	status.cpacket = *cpkt

	if status.wtime == 0 && status.ctime == 0 && status.wpacket == 0.0 && status.cpacket == 0.0 {
		status.threshold = false
	} else {
		status.threshold = true
	}

	check()
	fmt.Println(output())
	os.Exit(status.code)
}

func check() {
	// https://godoc.org/github.com/tatsushid/go-fastping
	pinger := fastping.NewPinger()
	ra, err := net.ResolveIPAddr("ip4:icmp", status.ip)
	if err != nil {
		error(UNK, "Error RESOLVIP")
	}
	pinger.AddIPAddr(ra)
	var count int = 0
	var rttTotal int64 = 0
	// Callbar recibir
	pinger.OnRecv = func(addr *net.IPAddr, rtt time.Duration) {
		count++
		rttTotal += rtt.Nanoseconds()
	}
	for i := 0; i < status.packets; i++ {
		err = pinger.Run()
		if err != nil {
			error(UNK, "Fallo al ejecutar el ping")
		}
	}
	if rttTotal != 0 {
		status.time = float64(rttTotal) / float64(1000000) / float64(count) // Nanoseconds to miliseconds
		status.pktpercent = (1 - float64(count)/float64(status.packets)) * 100
		if status.threshold {
			switch {
			// case status.ctime == 0 && status.wtime == 0:
			// status.code = OK // Ya es 0
			case status.ctime != 0 && status.time > status.ctime:
				status.code = CRIT
			case status.wtime != 0 && status.time > status.wtime:
				status.code = WARN
			}

			switch {
			// Comprobar que no haya sido puesto en un estado superior
			// case status.cpacket == 0 && status.wpacket == 0 && status.code == OK:
			//   status.code = OK  // Ya esta en OK o superior
			case status.cpacket != 0 && status.pktpercent > status.cpacket:
				status.code = CRIT // No es posible que haya superior
			case status.wpacket != 0 && status.pktpercent > status.wpacket && status.code < WARN:
				status.code = WARN
			}
		}
	} else {
		// No ha llegado ningun paquete, el porcentaje es del 100% perdidos
		status.pktpercent = 1.0
		status.code = CRIT
	}
}

func output() string {
	if status.code != UNK {
		if status.time != 0 {
			status.message = fmt.Sprintf("Responde time to %s %.3f ms, packets lost %.2f%%", status.ip, status.time, status.pktpercent*100)
		} else {
			status.message = fmt.Sprintf("No response from %s. 100%% packets lost", status.ip)
		}

		// perf data
		var perfData string = "|"
		if status.wtime != 0.0 {
			perfData = fmt.Sprintf("%s rtt=%.3fms;%.3fms;%.3fms;;", perfData, status.time, status.wtime, status.ctime)
		} else {
			perfData = fmt.Sprintf("%s rtt=%.3fms;;;;", perfData, status.time)
		}
		if status.cpacket != 0.0 {
			perfData = fmt.Sprintf("%s packetlost=%.2f%%;%.2f%%;%.2f%%;;", perfData, status.pktpercent*100, status.wpacket, status.cpacket)
		} else {
			perfData = fmt.Sprintf("%s packetlost=%.2f%%;;;;", perfData, status.pktpercent*100)
		}
		status.message += perfData
		return status.message
	} else {
		// UNK
		return status.message
	}
}

func error(code int, message string) {
	status.code = code
	status.message = message
	fmt.Println(output())
	os.Exit(code)
}
