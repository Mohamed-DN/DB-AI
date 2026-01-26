# Script per testare e configurare il monitoring sulle VM VirtualBox
# VM 1: 127.0.0.1:2200 (oracle)
# VM 2: 127.0.0.1:2201 (oracle)

$VMS = @(
    @{Name = "Oracle_VM1"; Host = "127.0.0.1"; SSHPort = 2200; User = "oracle"; Pass = "root" },
    @{Name = "Oracle_VM2"; Host = "127.0.0.1"; SSHPort = 2201; User = "oracle"; Pass = "root" }
)

Write-Host "🔍 Testing VirtualBox Oracle VMs" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

foreach ($vm in $VMS) {
    Write-Host "`n📡 Testing $($vm.Name) at $($vm.Host):$($vm.SSHPort)..." -ForegroundColor Yellow
    
    # Test SSH connectivity
    $testConnection = Test-NetConnection -ComputerName $vm.Host -Port $vm.SSHPort -WarningAction SilentlyContinue
    
    if ($testConnection.TcpTestSucceeded) {
        Write-Host "  ✅ SSH Port $($vm.SSHPort) is OPEN" -ForegroundColor Green
    }
    else {
        Write-Host "  ❌ SSH Port $($vm.SSHPort) is CLOSED" -ForegroundColor Red
        continue
    }
    
    # Test Oracle port (usually forwarded too)
    $oraclePort = $vm.SSHPort + 519  # 2200 -> 2719, 2201 -> 2720 (estimate)
    Write-Host "  ℹ️  To test Oracle, check if port 1521 is forwarded in VirtualBox" -ForegroundColor Cyan
}

Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Ensure Oracle port 1521 is forwarded in VirtualBox (e.g., 2521->1521, 2522->1521)"
Write-Host "2. Run the OEM scraper to test Oracle connection"
Write-Host "3. Configure MongoDB with VM details for auto-discovery"

Write-Host "`n🔧 Example commands:" -ForegroundColor Yellow
Write-Host 'python ops/scripts/oem_scraper.py --oracle-host 127.0.0.1 --oracle-port 2521 --oracle-sid ORCL --oracle-user system --oracle-pass root --once'
