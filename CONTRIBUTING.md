# Contributing

Review the following guidelines for submitting questions, issues, or changes to this repository.

## Questions

If you have issues using the SDK or have a question about the AppConfiguration service, you can ask a question on [Stack Overflow](https://stackoverflow.com/questions/tagged/ibm-appconfiguration). Be sure to include the `ibm-appconfiguration` tag.

## Issues

If you encounter an issue with the Python SDK, you are welcome to submit a [bug report](https://github.com/IBM/appconfiguration-python-sdk/issues).
Before that, please search for similar issues. It's possible somebody has encountered this issue already.

## Pull Requests

If you want to contribute to the repository, here's a quick guide:

1. Fork the repository
1. Install `virtualenv` and `tox`
1. Develop and test your code changes with [pytest].
    * Respect the original code [style guide][styleguide].
    * Only use spaces for indentation.
    * Create minimal diffs - disable on save actions like reformat source code or organize imports. If you feel the source code should be reformatted create a separate PR for this change.
    * Check for unnecessary whitespace with `git diff --check` before committing.
    * Make sure your code supports Python 3.5, 3.6 and 3.7. You can use `pyenv` and `tox` for this
    * You can run the style check by running the `pylint.sh` file in the `scripts` folder.
1. Make the test pass
1. Commit your changes
    * Commits should follow the [Angular commit message guidelines](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#-commit-message-guidelines). This is because our release tool uses this format for determining release versions and generating changelogs. To make this easier, we recommend using the [Commitizen CLI](https://github.com/commitizen/cz-cli) with the `cz-conventional-changelog` adapter.
1. Push to your fork and submit a pull request to the `master` branch

## Running the tests

You probably want to set up a [virtualenv].

1. Clone this repository:
    ```sh
    git clone https://github.com/IBM/appconfiguration-python-sdk.git
    ```
1. Install the sdk as an editable package using the current source:
    ```sh
    pip install --editable .
    ```
1. Install the SDK dependencies with:
    ```sh
    pip install -r requirements.txt
    ```
1. Install the test dependencies with:
    ```sh
    pip install -r requirements-dev.txt
    pip install pytest
    ```
1. Run the test cases with:
    ```sh
    pytest unit_tests
    ```

## Code coverage

The SDK is integrated with `coverage` to provide the test coverage report. Run the command `sh coverage-check.sh` in the `scripts` folder to generate the code coverage reports.

## Additional Resources

* [General GitHub documentation](https://help.github.com/)
* [GitHub pull request documentation](https://help.github.com/send-pull-requests/)

[dw]: https://developer.ibm.com/answers/questions/ask/?topics=appconfiguration
[stackoverflow]: http://stackoverflow.com/questions/ask?tags=ibm-appconfiguration
[styleguide]: http://google.github.io/styleguide/pyguide.html
[pytest]: http://pytest.org/latest/
[virtualenv]: http://virtualenv.readthedocs.org/en/latest/index.html

# Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
   have the right to submit it under the open source license
   indicated in the file; or

(b) The contribution is based upon previous work that, to the best
   of my knowledge, is covered under an appropriate open source
   license and I have the right under that license to submit that
   work with modifications, whether created in whole or in part
   by me, under the same open source license (unless I am
   permitted to submit under a different license), as indicated
   in the file; or

(c) The contribution was provided directly to me by some other
   person who certified (a), (b) or (c) and I have not modified
   it.

(d) I understand and agree that this project and the contribution
   are public and that a record of the contribution (including all
   personal information I submit with it, including my sign-off) is
   maintained indefinitely and may be redistributed consistent with
   this project or the open source license(s) involved.