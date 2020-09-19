cd C:\Users\opent
pwd
@{key = Get-Content ot2_ssh_key.pub | Out-String} | ConvertTo-Json | Invoke-WebRequest -Method Post -ContentType 'application/json' -Uri 169.254.2.6:31950/server/ssh_keys
pause