
param(
  [string]$remote = $(Throw("Parameter -remote is required")),
  [string]$name = $remote,
  [int]$number = 4,
  [array]$c = $null,
  [array]$w = $null
)

$res = Test-Connection $remote -Count $number

If ( $res -eq $null ) { Write-Host "2 PING-$($name) - CRIT - No data" }
Else {
  $mean = 0
  $success = 0
  ForEach ($ping in $res) {
    $mean += $ping.ResponseTime
    If ($ping.StatusCode -eq 0) { $success++ }
  }

  $packetlost = $success/$number * 100
  $mean /= $res.Length
  # No hay limites
  If ( $c -eq $null -and $w -eq $null ) { $status = 0 }
  ElseIf ( $mean -gt $c[0] -or $packetlost -gt $c[1] ) { $status = 2 }
  ElseIf ( $mean -gt $w[0] -or $packetlost -gt $w[0]) { $status = 1 }
  Else { $status = 0 }
}

<# Print #>
If  ( $c -eq $null -and $w -eq $null ) {
  $perf_data = "|rta=$($mean)ms;;; pl=$($packetlost)`%;;;"
} Else {
  $perf_data = " |rta=$($mean)ms;$($w[0]);$($c[0]); pl=$($packetlost)`%;$($w[1]);$($c[1]);"

}

If ( $status -eq 0 ) { Write-Host "$($status) PING_$($name) OK - Ping to $($remote) $($mean) ms. Packets lost $($packetlost)`% $perf_data"}

ElseIf ( $status -eq 1 ) { Write-Host "$($status) PING_$($name) WARN - Ping to $($remote) $($mean) ms (W: $($w[0]) ms). Packet lost $($packetlost)`% $perf_data" }

Else { Write-Host "$($status) PING_$($name) CRIT - Ping to $($remote) $($mean) ms!! (C: $($c[0]) ms). Packet lost $($packetlost)`% $perf_data" }
