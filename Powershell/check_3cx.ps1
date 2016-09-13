<# Check para servicios de la 3CX
  Para los propios de 720tec
  @Author: Borja Blasco <bblasco@720tec.es>
  @param:
    -services <servicio que se quiera monitorizar>
    -name <nombre del check>
    -v : Verbose
    -h : Ayuda
#>

param(
    [switch]$h = $false,
    [string]$services = $(Throw("Parameter -services is required")),
    [string]$name = "SERVICES",
    [switch]$v = $false
)

$vk = @() # Array de resultados OK
$warn = @() # Array de resultados WARN
$crit = @() # Array de resultados CRIT
$Status = 3 # Por defecto es UNK

If ( $h ) {
    Write-Host "Usage:`n`tcheck_services.ps1 -services `<service`> [-name `<name_service`> -v]"
    Write-Host "`n----------------------"
    Write-Host "This program is for check Windows services from the Check_MK Windows Agent."
    Write-Host "----------------------`n"
    Write-Host "-services `<services`> `tName of service or RegEx to match."
    Write-Host "-name `<service_name`> `tName for the check. If it is missing, it will name `"services`". It will be display in the monitor."
    Write-Host "-v `t Verbose mode, the output shows more information."
    Write-Host "-help `tDisplay this message"
    Write-Host "`n----------------------`n"
    Write-Host "More infomation in https://github.com/RataDP/checks"
    Exit
}

$list_serv = Get-Service -name $services # Obtener los servicios que cuadran con $services

ForEach( $serv in $list_serv ) {
   If ( $serv.StartType -ne "Automatic" ) {
        If ( $serv.Status -eq "Running" ) {
            $warn += $serv # El servicio no es Auto pero ejecutandose
            If ( $Status -ne 2 ) { $Status = 1 } # Si status no es CRIT pone en WARN
        } Else {
            $vk += $serv # El servicio no es Auto y no se ejecuta
        }
   } Else { # Esta en Auto
        If ($serv.Status -eq "Running" ) {
            $vk += $serv # Es auto y esta ejecutandose
        } Else {
            $crit += $serv # Es auto y no esta ejecutandose
            If ( $Status -ne 2 ) { $Status = 2 } # Si no esta CRIT pone CRIT
        }
   }
}

If ( $Status -eq 3 -and $warn.Count -eq 0 -and $crit.Count -eq 0 ) { $Status = 0 }

<# PRINT #>
If ( $Status -eq 0 ) { # OK
    If ($v -eq $false) { Write-Host "$($Status) $($name) - OK ($($vk.Count))" }
    Else { Write-Host "$($Status) $($name) - OK All the automatic services are running ($($vk.Count))" }
}

ElseIf ( $Status -eq 1 ) { # WARN
    If ($v -eq $false) { Write-Host "$($Status) $($name) - WARN - W ($($warn.Count)), OK ($($vk.Count))" }
    Else {
        Write-Host "$($Status) $($name) - WARN --W: ($($warn.Count)) " -NoNewline
        If ( $warn.Count -eq 1 ) { Write-Host " $($warn[0].Name)($($warn[0].Status)/$($warn[0].StartType))" -NoNewline }
        Else {
            ForEach ( $serv in $warn ) {
                If ( $serv -ne $warn[-1] ) {
                    Write-Host "$($serv.Name), " -NoNewline
                } Else { Write-Host "$($serv.Name)" -NoNewline }
            }
        }
        Write-Host " -OK: $($vk.Count)"
    }
}

Else { # CRIT
    If ($v -eq $false) { Write-Host "$($Status) $($name) - CRIT - C ($($crit.Count)), W ($($warn.Count)), OK ($($vk.Count))" }
    Else {
        Write-Host "$($Status) $($name) - CRIT - C: ($($crit.Count)) " -NoNewline
        If ( $crit.Count -eq 1 ) { Write-Host " $($crit[0].Name)($($crit[0].Status)/$($crit[0].StartType))" -NoNewline }
        Else {
            ForEach ( $serv in $crit ) {
                If ( $serv -ne $crit[-1] ) {
                    Write-Host "$($serv.Name), " -NoNewline
                } Else { Write-Host "$($serv.Name)" -NoNewline }
            }
        }
        Write-Host " -W: ($($warn.Count)) " -NoNewline
        If ( $warn.Count -eq 1 ) { Write-Host " $($warn[0].Name)($($warn[0].Status)/$($warn[0].StartType))" -NoNewline }
        Else {
            ForEach ( $serv in $warn ) {
                If ( $serv -ne $warn[-1] ) {
                    Write-Host "$($serv.Name), " -NoNewline
                } Else { Write-Host "$($serv.Name)" -NoNewline }
            }
        }
        Write-Host " -OK: ($($vk.Count))"
    }
}
