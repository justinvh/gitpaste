# GitPaste
GitPaste is a `GitHub Gist` clone.


## Quick Introduction

This is an alternative to gist.github.com. It allows you to deploy and create your own gist.github.com-like application. It is useful in an environment where you may not be able to use gist.github.com or alternatives.


## More Detailed Reasoning

> Why would company policies that ban github permit your alternative?

It's not a matter of being able to use github--there's no problem with it. There's an issue with posting code that does not have such permissible license. We're just simply not allowed to for a lot of the work. Sure, we could use private accounts, but we would still be violating the policy in a more devious manner. This allows anyone to deploy a gist.github-like setup on their local server where it can be isolated if needed.


## Dependencies

There's a requirements.txt. If you use pip then just follow the readme. 


## Forking and Testing

Fork on GitHub: https://github.com/justinvh/gitpaste

You can **try it out** here: http://www.gitpaste.com


## To-do:

    ✓ Add forking (fork anonymously!)
    ✓ Add downloading (you can download individual files)
    ✓ Add searching (uses Haystack and Whoosh 
    ✓ Add commenting (login to add comments) 
    ✓ Fix odd styling of line numbers (fixed widths, hacked resize())
    ✓ Adopting commits and pastes (login to adopt anonymous commits and pastes)
    ✓ Allowing tabbing in the textarea (you now can tab in the textarea! Huzzah)
    ✓ Post as anonymous directly (now you can remain anonymous even logged in, thanks not_mad_just_upset
    ✓ Add markdown support for comments
    ✓ Show diffs
    ✓ Fix some of the ordering issues (added sorting and priority-based pastes)
    ✓ Refine the user pages (masking email, anonymous, timezones)
    ✓ Add timezone support
    ✓ Preferences to hide email address
    ✓ Gravatar support (set USE_ICONS in settings.py to TRUE)
    ✓ Added repository downloading
    ✓ Private pastes
    ✓ Expiration on pastes
    ☐ Add embedding

    x Add cloning


# Refactoring Needed


    ☐ CSS is a disaster
    ☐ PEP8 everything


# Building
*Optional*: If you have virtualenv then create your desired environment.

    pip install -r requirements.txt
    cd saic
    python manage.py syncdb


# Running
Modify runserver.sh to fit your IP address needs.

    cd saic
    ./runserver.sh


# License
GitPaste is licensed under a three clause BSD License. See LICENSE.txt
