param(
    [string]$name = "Queue_Size",
    [switch]$h = $false,
    [int]$warn = $null,
    [int]$crit = $null
)

$queues = Get-WmiObject Exchange_SMTPQueue -Namespace "root/microsoftexchangev2"

If ($queues -eq $null) {
  $status = 3
} Else {
  $status = 0
  $wQueue = @{}
  $cQueue = @{}

  ForEach ($queue in $queues) {
    if ($c -ne $null -and $w -ne $null) {
      If ($queue.size -gt 0) {
        If ($queue.size -gt $c) {
          $status = 2
          $cQueue += @($queue.queuename, $queue.size)
        } Elseif ($queue.size -gt $w) {
          $status = 1
          $wQueue += $@($queue.queuename, $queue.size)
        }
      }
	}
  }
  If ($c -eq $null -and $w -eq $null) {
  $perf_data = ""
	  ForEach ($queue in $queues) {
		$perf_data += "$($queue.queuename)=$($queue.size)"
		If ($w -ne $null -and $c -ne $null) {
		  $perf_data += ";$($w);$($c)"
		}
		If ($queue -ne $queues[-1]) {
		  $perf_data += "|"
		}
	  }
   }
}

<# Print #>
If ($status -eq 0) {  Write-Host "$($status) $($name) $($perf_data) OK - All  queues OK" }
ElseIf ($status -eq 1) {
  Write-Host "$($status) $($name) $($perf_data) WARN - " -NoNewline
  ForEach ($w in $wQueue) {
    Write-Host "$($wQueue[0])=$($wQueue[1]) " -NoNewline
  }
}
ElseIf ($status -eq 2) {
  Write-Host "$($status) $($name) $($perf_data) CRIT - " -NoNewline
  ForEach ($w in $cQueue) {
    Write-Host "$($cQueue[0])=$($cQueue[1]) " -NoNewline
  }
}
Else {
  Write-Host "$($status) $($name) - UNK - Cannot get the queues"
}
