/**
 * @name F-string in logging statement
 * @description Detects use of f-strings in logging statements. Use lazy % formatting instead.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id sahabot2/f-string-in-logging
 * @tags maintainability
 *       anti-pattern
 *       logging
 *       performance
 */

import python

/**
 * Check if a call is a logging call (logger.info, logger.debug, etc.)
 */
predicate isLoggingCall(Call call) {
  exists(Attribute attr |
    call.getFunc() = attr and
    attr.getName() in ["debug", "info", "warning", "error", "critical", "exception"] and
    (
      // Instance logger (logger.info, log.debug, etc.)
      exists(Name logger | 
        attr.getObject() = logger and 
        (logger.getId().matches("%log%") or logger.getId().matches("%LOG%"))
      ) or
      // Module-level logging (logging.info, logging.debug, etc.)
      exists(Name logging_module |
        attr.getObject() = logging_module and
        logging_module.getId() = "logging"
      )
    )
  )
}

/**
 * Check if an expression is an f-string (formatted string literal)
 */
predicate isFString(Expr e) {
  exists(Fstring fs | fs = e)
}

from Call call, Expr arg
where
  isLoggingCall(call) and
  arg = call.getArg(0) and
  isFString(arg)
select call, "Use of f-string in logging statement. Use lazy % formatting instead: logger.info('Message %s', value)"
