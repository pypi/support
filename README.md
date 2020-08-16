# PyPI Support
This repository serves as an issue tracker for support requests related to using <https://pypi.org>.

## Issues which should be opened here

Any issue which relates to an individual user or project, or requires administrator or moderator intervention, should be opened here. For example:

* [PEP 541](https://www.python.org/dev/peps/pep-0541/) project name requests ([file a new issue](https://github.com/pypa/pypi-support/issues/new?template=pep541-request.md))
* Network access issues ([file a new issue](https://github.com/pypa/pypi-support/issues/new?template=access-issues.md))
* Upload limit requests ([file a new issue](https://github.com/pypa/pypi-support/issues/new?labels=limit+request&template=limit-request.md&title=Limit+Request%3A+PROJECT_NAME+-+60MB))
* Account recovery ([file a new issue](https://github.com/pypa/pypi-support/issues/new?labels=account-recovery&template=account-recovery.md&title=Account+recovery+request))
* etc.

## Issues which should _not_ be opened here
Any issue that affects how PyPI works for all users, or require code or configuration changes, should _not_ be opened here. For example:

* Feature requests
* Usability issues
* Bugs

These issues should be opened against [`pypa/warehouse`](https://github.com/pypa/warehouse/issues/new/choose) instead.

## Guidelines for upload limit requests
Generally, projects should try to minimize the size of their distributions as
much as possible. Large distributions consume significant amounts of PyPI's
resources, and also generally do not provide a good user experience.

Small (60MB-120MB) upload limits are generally granted for the following reasons:
* project contains small pre-trained models
* project contains a small JAR file
* any other sufficiently motivated reason

Large (120MB+) upload limits are generally granted for the following reasons:
* project contains large compiled binaries to maintain platform/architecture/GPU support
* project is associated with an established project or organization

Upload limits are generally denied for the following reasons:
* project makes nightly releases and/or is published frequently
* project contains large pre-trained machine learning models
* project includes a large JAR file
* project includes a runtime for another programming language
* project is not associated with an established project or organization
* project has not made a best-effort to reduce release size

## Security policy
To read the most up to date version of our security policy, including directions for submitting security vulnerabilities, please visit <https://pypi.org/security/>.

## If you are unsure where to file your issue
Please [create a new issue here](https://github.com/pypa/pypi-support/issues/new/choose) and it will be transferred as necessary.

## Code of Conduct
Everyone interacting in the PyPI's codebases, issue trackers, chat rooms, and mailing lists is expected to follow the [PSF Code of Conduct](https://github.com/pypa/.github/blob/main/CODE_OF_CONDUCT.md).
