/**
 * @name Inline import statements
 * @description Detects import statements inside functions. Imports should be at module level.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id sahabot2/inline-imports
 * @tags maintainability
 *       anti-pattern
 *       readability
 */

import python

/**
 * Check if an import is inside a function (not at module level)
 */
predicate isInlineImport(Import imp) {
  exists(Function f | imp.getScope() = f)
}

/**
 * Check if an import from is inside a function (not at module level)
 */
predicate isInlineImportFrom(ImportExpr imp) {
  exists(Function f | imp.getScope() = f)
}

from Stmt imp
where
  (isInlineImport(imp) or isInlineImportFrom(imp)) and
  not imp.getLocation().getFile().getRelativePath().matches("%/tests/%") and
  not imp.getLocation().getFile().getRelativePath().matches("%test_%.py")
select imp, "Import statement inside function. Move imports to module level for better readability and performance."
