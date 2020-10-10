# Countdown

A timeout function to encrypt sensitive data.

When running, an interface will let you submit a password to reset the timer. 
After 7 days, an email is sent and the password should be entered.
If nothing is done, another email is sent the next day.
If still nothing, the concerned directories are encrypted into a passworded 7z archive, then securely wiped (as securely as a journaled filesystem allows anyway.
I don't have the understanding and knowledge to really eliminate everything from a disk)

Worth knowing, the password to decrypt the archive -- in case you're not actually dead and just didn't have any internet for over a week -- is the hashed form of the interface password. Algorithm is SHA-512.

The files should be owned, readable and executable by root only (700), otherwise the password (stored in data.xml in its hashed form) can be recovered.

If any issue, just delete data.xml and open the interface again. Should allow you to configure things again (password, email, storage location and target directories).

This works on a Unix environment for now, as the sendmail function isn't working on Windows.
I may push an update for this, on the other hand I don't really care about Windows.
