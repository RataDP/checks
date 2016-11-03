<#
  Check para comprobar una resolución DNS en Windows

  @lastModified: 07/06/2016
  @Author: Borja Blasco `<bblasco@720tec.es`>
  @param:
    -name `<Nombre a resolver`>
    -dname `<Nombre para el servicio`>
    -r `<r a comparar`>
    -h Ayuda
#>

param(
    [switch]$h = $false,
    [string]$name = $(Throw("Parameter -name is required")),
    [string]$dname = $name,
    [string]$r = $(Throw("Parameter -r is required")),
    [string]$type = "A"
)

If ( $h ) {
    Write-Host "Usage:`n`tcheck_dns.ps1 -name `<FQDN`> [-dname `<name_service`>] -r `<ip_to_compare`>"
    Write-Host "`n----------------------"
    Write-Host "This program is for check Windows DNS resolution from the Check_MK Windows Agent."
    Write-Host "----------------------`n"
    Write-Host "-name `<FQDN`> `tName to test de DNS"
    Write-Host "-dname `<service_name`> `tName for the check name. If it is missing will name as -name value. It will be display in the monitor."
    Write-Host "-r `<ip`> `tIP to compare the results."
    Write-Host "-type `<type`> `tType of resolution name. Default is A"
    Write-Host "-help `tDisplay this message"
    Write-Host "`n----------------------`n"
    Write-Host "More infomation in https://github.com/RataDP/checks"
    Exit
}

<# Fetching data #>
$res = Resolve-DnsName -Name $name -Type $type 2> Out-Null

<# Check #>
$status = 3
If ( $res -eq $null ) { $status = 2 } # Critical
Else {
  If ( $res -isnot [System.Array] ) {
    If ( $res.IPAddress -eq $r ) { $status = 0 }
    Else { $status = 2 }
  } Else { # Es lista
    Foreach ( $item in $res ) {
      If ( $item)
    }
<#
    PRINT output
#>
# CRIT - No hay servidor DNS o no hay resolucion
If ( $res -eq $null ) { Write-Host "2 DNSResolve-$($dname) - CRIT - $($Error[0].Exception.Message)" }
# OK - Resolution == Esperado
ElseIf ( $res.IPAddress -eq $r ) { Write-Host "0 DNSResolve-$($dname) - OK - Successful resolution. Got: $($res.IPAddress)" }
# CRIT - Resolution != Esperado
Else{ Write-Host "2 DNSResolve-$($dname) - CRIT - Wrong resolution. Got: $($res.IPAddress) Expected: $($r)" }
