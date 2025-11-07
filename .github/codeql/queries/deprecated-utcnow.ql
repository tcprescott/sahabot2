/**
 * @name Use of deprecated datetime.utcnow()
 * @description Detects use of deprecated datetime.utcnow(). Use datetime.now(timezone.utc) instead.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id sahabot2/deprecated-utcnow
 * @tags maintainability
 *       anti-pattern
 *       deprecation
 */

import python

from Call call, Attribute attr
where
  call.getFunc() = attr and
  attr.getName() = "utcnow" and
  exists(Name datetime_module |
    attr.getObject() = datetime_module and
    datetime_module.getId() = "datetime"
  )
select call, "Use of deprecated datetime.utcnow(). Use datetime.now(timezone.utc) instead."
