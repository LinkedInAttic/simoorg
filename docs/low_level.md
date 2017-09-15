# LOW LEVEL FAILURES
Libfui provides an easy way to induce low level failures to any POSIX call in your application. To be able to use low level failures against POSIX calls, we require the application to be started under the control of libfiu. The best practice is to use these failures either on your staging/dev clusters or run on select nodes from your production cluster.

Please check the [libfiu website](https://blitiri.com.ar/p/libfiu/) to understand how to build and install libfiu on your servers. Once the libfiu packages are installed, please restart your application under the control of libfiu. You can achieve this using the [fiu-run command](https://blitiri.com.ar/p/libfiu/doc/man-fiu-run.html), the command should look something like the following
```
fiu-run -x -c $COMMAND
```
$COMMAND contains the path of your application binary.

Once you have your nodes set up, also make sure the failure scripts “posix_failure.sh and posix_revert.sh” are present on the nodes in question as well. Next update the fate book, by first adding failure definition to the failures section. You can find sample posix failure definitions in the sample_config.

```
  - name: certain_write_failure
    induce_handler:
      type: ShellScriptHandler
      coordinate: /home/test/failure_scripts/base/posix_failure.sh
      arguments: ['/usr/local/test_app/test.pid', 'posix/io/rw/pwrite64', 1, '/usr/local/libfui/bin']
    restore_handler:
      type: ShellScriptHandler
      coordinate: /home/test/failure_scripts/base/posix_revert.sh
      arguments: ['/usr/local/test_app/test.pid', 'posix/io/rw/pwrite64', '/usr/local/libfui/bin']
    wait_seconds: 5
    sudo_user: test
```

First, the handler type for the definition should be set to ShellScriptHandler. The coordinates should be set to the locations of posix_failure.sh and posix_revert.sh on your servers of choice. For induce_handler the arguments should be as follows

* argument1 : The pid file (file containing the pid of your application)
* argument2 : The posix call you will be inducing failures for
* argument3 : The probability with which failures will happen (values [0 - 1])
* argument4 : The path to libfiu bin files

For revert_handler the arguments should be as follows
* argument1 : The pid file (file containing the pid of your application)
* argument2 : The posix call you will be inducing failures for
* argument3 : The path to libfiu bin files


Next add the new failure names in the failure list in the destiny section of the fate book. Now we have completed the fate book updates and we can go ahead and start Simoorg.
