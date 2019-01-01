# Tips for a successful Pull Request
1. Bonus: Randomly generate IPv6 prefix for new allocations to avoid RFC4193 section 3.2. violation ([script](https://git.dn42.us/netravnen/dn42-repo-utils/raw/7b9e26d0ef4b2b6c68c4370ef65d8d7f5da76493/ulagen.py))
2. Squash your commits -- Keep the changes simple to read.
3. Run the schema check -- Make sure the changes are valid! Run `./check-my-stuff YOUROWN-MNT`
4. BONUS: install the commit hook! Run `./install-commit-hook YOUROWN-MNT`
5. Sign your commit -- Makes it easier to verify. 
6. Bonus: add your pgp fingerprint to your MNT `auth:      pgp-fingerprint  <pgp-fingerprint>` [[See XUU-MNT example](data/mntner/XUU-MNT)]
7. ???
8. Profit!

