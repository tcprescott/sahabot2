/**
 * @name None user_id in event emission
 * @description Detects use of None for user_id in event emissions. Use current_user.id or SYSTEM_USER_ID instead.
 * @kind problem
 * @problem.severity error
 * @precision medium
 * @id sahabot2/none-user-id-in-events
 * @tags maintainability
 *       anti-pattern
 *       correctness
 */

import python

/**
 * Check if a call is an EventBus.emit call
 */
predicate isEventEmit(Call call) {
  exists(Attribute attr |
    call.getFunc() = attr and
    attr.getName() = "emit" and
    exists(Name eventbus |
      attr.getObject() = eventbus and
      eventbus.getId() = "EventBus"
    )
  )
}

/**
 * Check if an event constructor has user_id=None
 */
predicate hasNoneUserId(Call eventCall) {
  exists(Keyword kw |
    kw = eventCall.getAKeyword() and
    kw.getArg() = "user_id" and
    kw.getValue() instanceof None
  )
}

from Call emitCall, Call eventCall
where
  isEventEmit(emitCall) and
  eventCall = emitCall.getArg(0) and
  hasNoneUserId(eventCall)
select emitCall, "Event emission with user_id=None. Use current_user.id for user actions or SYSTEM_USER_ID for system actions."
