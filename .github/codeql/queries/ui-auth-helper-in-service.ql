/**
 * @name UIAuthorizationHelper in service layer
 * @description Detects use of UIAuthorizationHelper in service layer. Use policy framework directly instead.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id sahabot2/ui-auth-helper-in-service
 * @tags maintainability
 *       anti-pattern
 *       architecture
 */

import python

/**
 * Check if a file is a service file
 */
predicate isServiceFile(File f) {
  f.getRelativePath().matches("application/services/%.py")
}

/**
 * Check if an import imports UIAuthorizationHelper
 */
predicate importsUIAuthorizationHelper(ImportMember imp) {
  imp.getModule().getName() = "application.services.ui_authorization_helper" and
  imp.getName() = "UIAuthorizationHelper"
}

/**
 * Check if a class instantiation is UIAuthorizationHelper
 */
predicate instantiatesUIAuthorizationHelper(Call call) {
  exists(Name name |
    call.getFunc() = name and
    name.getId() = "UIAuthorizationHelper"
  )
}

from AstNode node
where
  (importsUIAuthorizationHelper(node) or instantiatesUIAuthorizationHelper(node)) and
  isServiceFile(node.getLocation().getFile())
select node, "Use of UIAuthorizationHelper in service layer. Use policy framework (OrganizationPermissions) directly instead."
