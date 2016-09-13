<# 
  Check para comprobar una resolución DNS en Windows

  @lastModified: 07/06/2016
  @Author: Borja Blasco `<bblasco@720tec.es`>
  @param:
    -name `<Nombre a resolver`>
    -dname `<Nombre para el servicio`>
    -ip `<Ip a comparar`>
#>

param(
    [switch]$help = $false,
    [string]$name = $(Throw("Parameter -name is required")),
    [string]$dname = $name,
    [string]$ip = $(Throw("Parameter -ip is required"))
)

If ( $help ) {
    Write-Host "Usage:`n`tcheck_dns.ps1 -name `<FQDN`> [-dname `<name_service`>] -ip `<ip_to_compare`>"
    Write-Host "`n----------------------"
    Write-Host "This program is for check Windows DNS resolution from the Check_MK Windows Agent."
    Write-Host "----------------------`n"
    Write-Host "-name `<FQDN`> `tName to test de DNS"
    Write-Host "-dname `<service_name`> `tName for the check name. If it is missing will name as -name value. It will be display in the monitor."
    Write-Host "-ip `<ip`> `tIP to compare the results."
    Write-Host "-help `tDisplay this message"
    Write-Host "`n----------------------`n"
    Write-Host "More infomation in `$MyGithub"
    Exit
}

$res = Resolve-DnsName -Name $name 2> Out-Null

<#
    PRINT output
#>
# CRIT - No hay servidor DNS o no hay resolucion
If ( $res -eq $null ) { Write-Host "2 DNSResolve-$($dname) - CRIT - $($Error[0].Exception.Message)" }
# OK - Resolution == Esperado
ElseIf ( $res.IPAddress -eq $ip ) { Write-Host "0 DNSResolve-$($dname) - OK - Successful resolution. Got: $($res.IPAddress)" }
# CRIT - Resolution != Esperado
Else{ Write-Host "2 DNSResolve-$($dname) - CRIT - Wrong resolution. Got: $($res.IPAddress) Expected: $($ip)" }