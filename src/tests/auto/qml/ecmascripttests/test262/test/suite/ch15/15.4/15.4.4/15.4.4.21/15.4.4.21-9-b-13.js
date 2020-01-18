/// Copyright (c) 2012 Ecma International.  All rights reserved. 
/// Ecma International makes this code available under the terms and conditions set
/// forth on http://hg.ecmascript.org/tests/test262/raw-file/tip/LICENSE (the 
/// "Use Terms").   Any redistribution of this code must retain the above 
/// copyright and this notice and otherwise comply with the Use Terms.
/**
 * @path ch15/15.4/15.4.4/15.4.4.21/15.4.4.21-9-b-13.js
 * @description Array.prototype.reduce - deleting own property with prototype property in step 8 causes prototype index property to be visited on an Array
 */


function testcase() {

        var testResult = false;

        function callbackfn(accum, val, idx, obj) {
            if (idx === 1 && val === 1) {
                testResult = true;
            }
        }
        var arr = [0, 111];

        Object.defineProperty(arr, "0", {
            get: function () {
                delete arr[1];
                return 0;
            },
            configurable: true
        });

        try {
            Array.prototype[1] = 1;
            arr.reduce(callbackfn);
            return testResult;
        } finally {
            delete Array.prototype[1];
        }
    }
runTestCase(testcase);
