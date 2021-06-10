# Countdown

A timeout function to encrypt sensitive data in case of an early disappearance or something.
The idea came after reading about some guy having searched through a deceased relative's computer for whatever documents or family memorabilia, and stumbled upon, well, other things he'd rather hadn't known about.
Just to be clear, I have no such stuff, so the whole projet is purely for the sake of developing something new.

When running, an interface will let you submit a password to reset the timer. The first run leads to a configuration page where to set up different items: password, email, storage location and target directories. 
These are stored in a data.xml file. Password is stored in a hashed form.

After 7 days, an email is sent and the password should be entered to reset the timer.
If nothing is done, another email is sent the next day.
If still nothing, the concerned directories are encrypted into a passworded 7z archive, then alls archives are encrypted again in a final 7z file. Didn't really mean to do that but the python library wouldn't let me append directories to an existing archive.

All targets and intermediary archives are then securely wiped (as securely as a journaled filesystem allows anyway. I don't have the understanding and knowledge to really eliminate everything from a disk).
As this time, system only handles local directories. Should be possible to add support for remote locations but I don't have the use for that.  

<b>Worth knowing, the password to decrypt the archive -- in case you're not actually dead and just didn't have any internet for over a week -- is the hashed form of the interface password. Algorithm is SHA-512.</b>

The files should be owned, readable and executable by root only (700), otherwise the password (stored in data.xml) can be recovered, although in its hashed form, so it won't allow access to the interface itself (which requires the plaintext password).

Doesn't sound too practical but I couldn't find a better way.

If any issue, just delete data.xml and open the interface again. Should allow you to configure things again.

This works on a Unix environment for now, as the sendmail function isn't working on Windows.
I may push an update for this, on the other hand I don't really care about Windows.

Note: the sender email adress is hardcoded in line 112 of countdown.py. Change it to whatever works for you.
Note2: unless a mail server is properly configured, anything pushed by sendmail will be flagged as spam by any service provider. Whitelist or something.
