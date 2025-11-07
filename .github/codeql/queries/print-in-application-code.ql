/**
 * @name Use of print() in application code
 * @description Detects use of print() for logging in application code. Use logging framework instead.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id sahabot2/print-in-application-code
 * @tags maintainability
 *       anti-pattern
 *       logging
 */

import python

/**
 * Check if a file is an application code file (not a test, tool, or demo script).
 */
predicate isApplicationCode(File f) {
  not f.getRelativePath().matches("%/tests/%") and
  not f.getRelativePath().matches("%/tools/%") and
  not f.getRelativePath().matches("%test_%.py") and
  not f.getRelativePath().matches("%_test.py") and
  not f.getRelativePath().matches("setup_test_env.py") and
  not f.getRelativePath().matches("demo_%.py") and
  not f.getRelativePath().matches("check_%.py") and
  not f.getRelativePath().matches("%/migrations/%")
}

from Call call, Name func
where
  call.getFunc() = func and
  func.getId() = "print" and
  isApplicationCode(call.getLocation().getFile())
select call, "Use of print() in application code. Use logging framework instead (logger.info, logger.debug, etc.)."
