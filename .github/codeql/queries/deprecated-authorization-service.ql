/**
 * @name Use of deprecated AuthorizationService
 * @description Detects use of deprecated AuthorizationService. Use UIAuthorizationHelper or Permission enum instead.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id sahabot2/deprecated-authorization-service
 * @tags maintainability
 *       anti-pattern
 *       deprecation
 */

import python

/**
 * Check if an import imports AuthorizationService
 */
predicate importsAuthorizationService(ImportMember imp) {
  imp.getModule().getName() = "application.services.authorization_service" and
  imp.getName() = "AuthorizationService"
}

/**
 * Check if a class instantiation is AuthorizationService
 */
predicate instantiatesAuthorizationService(Call call) {
  exists(Name name |
    call.getFunc() = name and
    name.getId() = "AuthorizationService"
  )
}

from AstNode node
where
  importsAuthorizationService(node) or
  instantiatesAuthorizationService(node)
select node, "Use of deprecated AuthorizationService. In UI layer, use UIAuthorizationHelper for organization permissions or Permission enum for global permissions. In service layer, use policy framework directly."
