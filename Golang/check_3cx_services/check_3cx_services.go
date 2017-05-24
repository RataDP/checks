package main

import (
	"fmt"
	"os"
	"os/exec"
	"regexp"
	"strings"
)

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
    Check 3CX services
    Version 0.2

USAGE: check_3cx-services
*/

type service struct {
	name        string
	load        string
	active      string
	state       string
	description string
}

type checkStatus struct {
	code             int
	servicesDown     []string
	servicesDisabled []string
	down             int
	disabled         int
}

const (
	OK   = 0
	WARN = 1
	CRIT = 2
	UNK  = 3
)

func main() {
	sysctlCmd := exec.Command("bash", "-c", "systemctl list-units 3CX* | grep 3CX")
	outputCmd, err := sysctlCmd.Output()
	if err != nil {
		panic("No se pudo ejecutar")
	}

	var services []service
	var lineSplit []string
	var status checkStatus
	split := strings.Split(string(outputCmd), "\n")
	rexpSpaceInside := regexp.MustCompile(`[\s\p{Zs}]{2,}`)
	for _, line := range split {
		line = rexpSpaceInside.ReplaceAllString(line, " ")
		lineSplit = strings.SplitN(line, " ", 5)
		// 0 - nombre, 1 - load, 2 - active, 3 - running, 4 - descr
		// lineSplit[0] = lineSplit[0][:len(lineSplit[0])-8] // Quitar .service
		if len(lineSplit) >= 5 {
			services = append(services, service{lineSplit[0][:len(lineSplit[0])-8], lineSplit[1], lineSplit[2], lineSplit[3], lineSplit[4]})
		}
	}

	check(&status, services)    // Se le pasa el punto de status
	fmt.Println(output(status)) // No se pasa el puntero porque no modifica
	os.Exit(status.code)

}

// Se le pasa un puntero porque si no no actualiza la misma estructura, crea otra.
func check(status *checkStatus, svcs []service) {
	var svDown, svDisabled []string
	var down, disabled int
	if len(svcs) == 0 {
		status.code = UNK
		return
	}
	for _, svc := range svcs {
		if svc.state != "running" {
			// No están ejecutándose
			status.code = CRIT
			down++
			svDown = append(svDown, svc.name)
		}
		if svc.load != "loaded" {
			// Están ejecutándose pero no son automáticos
			disabled++
			svDisabled = append(svDisabled, svc.name)
			if status.code < WARN {
				status.code = WARN
			}
		}
	}

	status.disabled = disabled
	status.down = down
	status.servicesDisabled = svDisabled
	status.servicesDown = svDown

	return

}

// No se pasa el puntero porque no modifica
// Salida: STATUS_STR - Message |perfdata
func output(status checkStatus) string {
	outFormat := "%s - %s |down=%d|disabled=%d"
	message := ""
	svcs := ""
	if status.code != UNK {
		if status.code == OK {
			message = "All services are running and enabled"
		} else {
			// Es error or warn
			if status.down <= 0 { // No hay downs
				if status.disabled > 1 { // Plural
					svcs = strings.Join(status.servicesDisabled, ", ")
					message = fmt.Sprintf("There are %d (%s) services disabled", status.disabled, svcs)
				} else if status.disabled == 1 { // Singular
					message = fmt.Sprintf("There is 1 (%s) service disabled", status.servicesDisabled[0])
				}
			} else if status.disabled <= 0 { // No hay disableds
				if status.down > 1 { // Plural
					svcs = strings.Join(status.servicesDown, ", ")
					message = fmt.Sprintf("There are %d (%s) services down", status.down, svcs)
				} else if status.down == 1 { // Singular
					message = fmt.Sprintf("There is 1 (%s) service down", status.servicesDown[0])
				}
			} else { // Hay de los dos
				var svcDi, svcDo string
				svcDi = strings.Join(status.servicesDisabled, ", ")
				svcDo = strings.Join(status.servicesDown, ", ")

				message = fmt.Sprintf("There are %d (%s) services down and %d (%s) services disabled", status.down, svcDo, status.disabled, svcDi)
			}
		}
	} else {
		message = "Something has failed"
	}

	statusString := ""
	switch status.code {
	case UNK:
		statusString = "UNK"
	case OK:
		statusString = "OK"
	case WARN:
		statusString = "WARN"
	case CRIT:
		statusString = "CRIT"
	}

	return fmt.Sprintf(outFormat, statusString, message, status.down, status.disabled)
}
