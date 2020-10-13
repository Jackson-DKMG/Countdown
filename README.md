# Countdown

A timeout function to encrypt sensitive data in case of an early disappearance of something.
The idea came after reading about some guy having searched a deceased relative's computer for whatever documents or family memorabilia, and stumbled upon a shitload of kid porn or something.
Just to be clear, I have no such stuff (but thanks for wondering), at worst pictures of my wife in underwear, so the whole projet is purely for the sake of developing something new.

When running, an interface will let you submit a password to reset the timer. The first run leads to a configuration page where to set up different items: password, email, storage location and target directories. 
These are stored in a data.xml file. Password is stored in a hashed form.

After 7 days, an email is sent and the password should be entered to reset the timer.
If nothing is done, another email is sent the next day.
If still nothing, the concerned directories are encrypted into a passworded 7z archive, then alls archives are encrypted again in a final 7z file. Didn't really mean to do that but the python library wouldn't let me append directories to an existing archive.

All targets and intermediary archives are then securely wiped (as securely as a journaled filesystem allows anyway. I don't have the understanding and knowledge to really eliminate everything from a disk.
As this time, system only handles local directories. Should be possible to add support for remote locations but I don't have the use for that.  

Worth knowing, the password to decrypt the archive -- in case you're not actually dead and just didn't have any internet for over a week -- is the hashed form of the interface password. Algorithm is SHA-512.
The files should be owned, readable and executable by root only (700), otherwise the password (stored in data.xml) can be recovered.

Doesn't sound too safe but I couldn't find a better way. Maybe use a reversible algorithm for obfuscating the password, but then again if the files are readable then anyone can decrypt the hashed password.


If any issue, just delete data.xml and open the interface again. Should allow you to configure things again.

This works on a Unix environment for now, as the sendmail function isn't working on Windows.
I may push an update for this, on the other hand I don't really care about Windows.

Note: the sender email adress is hardcoded in line 112 of countdown.py. Change it to whatever works for you.
