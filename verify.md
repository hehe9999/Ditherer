# Verifying The Binary
## Prerequisites
**1. [Git for Windows](https://git-scm.com/downloads/win)**
* Required to use `sha256sum`
* During installation, **choose "Use Git from the command line and also from 3rd-party software"** to enable system-wide use.

**2. [GPG](https://gpg4win.org/)**
* Install this to get `gpg`
* During install, ensure the **GnuPG component** is selected.

**3. The following 3 files from the latest release on the [Releases](https://github.com/hehe9999/Ditherer/releases) page:**
* `dither.exe` - the binary
* `dither.exe.sha256` - the SHA256 checksum
* `dither.exe.sha256.asc` - the GPG signature for the checksum

**4. The project's public GPG key**
* Available in the repository [here](/gpg/gpg-public-key.asc)

## Step-by-Step Verification
**1. Import the public GPG key**

Open **Command Prompt or Git Bash** in the directory containing the three files, then run:
```bash
gpg --import gpg-public-key.asc
```
You should see a message about the key being successfully imported.

**2. Verify the GPG signature**
```bash
gpg --verify dither.exe.sha256.asc dither.exe.sha256
```
If successful, it will output a message saying:
```
Good signature from "Jerad Rhinehart <jeradrhinehart@gmail.com>"
```

**3. Verify the SHA256 checksum**

Open **Git Bash** in the directory containing the three files
```bash
sha256sum -c dither.exe.sha256
```
This checks the actual binary against the checksum file. Output should be:
```
dither.exe: OK
```
If the hash does *not* match, you'll get:
```
dither.exe: FAILED
sha256sum: WARNING: 1 computed checksum did NOT match
```
**If you see the *FAILED* message, do *not* run the program. It may have been corrupted or tampered with.**

## Why do this?
* **GPG Signature** = Verifies the checksum hasn't been tampered with.
* **SHA256 Checksum** = Verifies the `.exe` file matches the one I released.
* **Built with GitHub Actions + SLSA 3** = The release was automatically compiled from this source code and cryptographically linked to it.