# SSH Auto-setup script menggunakan plink atau OpenSSH dengan expect
# Menggunakan .NET Process untuk kirim password ke stdin

param(
    [string]$Host    = "telur",
    [string]$User    = "telur",
    [string]$Pass    = "telur",
    [string]$Command = "echo ok"
)

# Coba pakai plink jika ada
$plink = Get-Command plink -ErrorAction SilentlyContinue
if ($plink) {
    & plink -ssh -batch -pw $Pass "$User@$Host" $Command
    return
}

# Fallback: pakai OpenSSH dengan sshpass-equivalent via Process
Add-Type -TypeDefinition @"
using System;
using System.Diagnostics;
using System.Threading;

public class SshRunner {
    public static int Run(string host, string user, string pass, string command) {
        var psi = new ProcessStartInfo {
            FileName = "ssh",
            Arguments = String.Format("-o StrictHostKeyChecking=no -o PasswordAuthentication=yes {0}@{1} \"{2}\"", user, host, command),
            UseShellExecute = false,
            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true
        };
        var p = Process.Start(psi);
        // Kirim password
        Thread.Sleep(2000);
        p.StandardInput.WriteLine(pass);
        p.StandardInput.Flush();
        
        string output = p.StandardOutput.ReadToEnd();
        string error  = p.StandardError.ReadToEnd();
        p.WaitForExit();
        
        Console.Write(output);
        Console.Error.Write(error);
        return p.ExitCode;
    }
}
"@

[SshRunner]::Run($Host, $User, $Pass, $Command)
