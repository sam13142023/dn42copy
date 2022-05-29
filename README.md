# Guide for creating a Pull Request

The dn42 registry is a git repository and changes are made to it using pull requests.

There are many public guides available on how to work with remote git repositories,  
e.g. [git documentation](https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes) or [guide at github](https://help.github.com/en/github/using-git)

1. **Fork the registry repo, then clone your fork to create a local working copy**

Use the `Fork` button in the gitea UI (at the top right of the repository page), then:

```sh
git clone git@git.dn42.dev:<FOO>/registry.git
```

Where `<FOO>` is your gitea username.

2. **Make changes in your local copy**

See the [getting started](https://dn42.dev/howto/Getting-Started) guide in the [Wiki](https://dn42.dev) for more information.

- `inet6num` must have a random prefix to satisfy [RFC4193](https://tools.ietf.org/html/rfc4193)
- Include an [auth method](https://dn42.dev/howto/Registry-Authentication) in your MNTNER so you changes to your objects can be authenticated
- Run the schema checking tools to validate your changes
  - `./fmt-my-stuff MNTNER-MNT`
  - `./check-my-stuff MNTNER-MNT`
  - `./check-pol origin/master MNTNER-MNT`

```sh
$EDITOR <change some stuff>
git add .
git commit -S
```

3. **Push your changes back to your forked copy of the registry**

 - You must squash multiple commits together
 - You must also sign the final commit using your MNTNER [authentication method](https://dn42.dev/howto/Registry-Authentication).
 
Whilst not essential, it is also good practice to rebase your work on top of any other changes that may have happened on the master branch of the registry.

The registry contains a script that can automatically rebase and squash your commits:

```sh
./squash-my-commits -S --push
```

or you can do it manually:

```sh
# Add the main registry repository as another remote, you only need to do this once

git remote add dn42registry git@git.dn42.dev:dn42/registry.git

# make sure its up to date

git fetch dn42registry master

# rebase your local copy on top of the registry master
#
# -i to interactively pick the commits
# -S to sign the result with your GPG key (not required for SSH authentication)
#
# In interactive mode, make sure the first commit says 'pick'
# change the rest from 'pick' to 'squash'
# save and close to create the commit

git rebase -i -S dn42registry/master

# force push your changes back to your registry copy

git push --force
```

If you forget to sign your commit you can sign the existing commit using:

```sh
git commit --amend --no-edit -S
git push --force
```

4. **Create a pull request**

In the gitea GUI, select your fork, check your changes again for a final time and then hit the 'Pull Request' button.

Your changes will go through a number of automatic checks before a final manual review by the registry maintainers. Manual reviews are typically completed once a day.

5. **Making updates**

If you need to make changes to fix review issues simply make the updates to your fork and follow the process in (3) to rebase, squash and sign your changes again. **You must do this for every update**.

**Do not close and re-open a new pull request**, any changes you make on your branch will be automatically updated in the PR. Creating a new PR loses all the history and makes tracking changes harder.

6. **Tidy Up**

Once your changes have been accepted and merged, you may delete your local copy and the fork that was created in gitea.

# Gitea Usage

The DN42 registry is a community resource for *your* benefit.
Registered users are free to create and use their own repositories and use the Drone CI tools, but please be considerate in your usage.

 - Repositories should be related to DN42
 - Do not create tools that make regular, automated, push changes to repositories unless agreed with the registry maintainers
 - Do not just create a mirror of other, publically available, repositories

# Data Privacy

Gitea and the DN42 registry contains personal information for users who are registered in DN42; this information is stored in Canada and viewable by any registered member. In addition, anyone with access to the repository is able to make their own copies of the registry, which they may then process or transfer in arbitrary ways. You must assume that all data entered in to the registry cannot be kept private and will be made publically available. 

Any personal information stored in the registry is optional and voluntarily provided by you. Whilst the registry maintainers will make best efforts to update or delete personal data, you must accept that the technical restrictions of git may make this impossible and that your information will likely have been distributed beyond the control of the registry maintainers.  

If this is not acceptable for you, you must not upload your personal details to the registry.

All registered users have the capability to make copies of the registry data for their own use. If you do copy the registry you must ensure that any copies you make are deleted when no longer required and that you will make best efforts to update or delete personal data when requested.

You **must not** clone or mirror the registry in to a commercial git repository; commercial terms of service can be incompatible with the use of personal data in the registry.