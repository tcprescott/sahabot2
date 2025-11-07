/**
 * @name Direct ORM access from UI/API routes
 * @description Detects direct ORM model queries in UI pages or API routes. Use services instead.
 * @kind problem
 * @problem.severity error
 * @precision medium
 * @id sahabot2/orm-in-ui-api
 * @tags maintainability
 *       anti-pattern
 *       architecture
 */

import python

/**
 * Check if a file is a UI page or API route
 */
predicate isUIOrAPIFile(File f) {
  f.getRelativePath().matches("pages/%.py") or
  f.getRelativePath().matches("api/routes/%.py") or
  f.getRelativePath().matches("views/%.py")
}

/**
 * Check if a call is an ORM query operation
 */
predicate isORMQuery(Call call) {
  exists(Attribute attr, Name model |
    call.getFunc() = attr and
    attr.getObject() = model and
    // Common ORM query methods
    attr.getName() in [
      "get", "filter", "all", "create", "update", "delete",
      "get_or_none", "first", "exists", "count",
      "update_or_create", "bulk_create", "bulk_update",
      "select_related", "prefetch_related", "values", "values_list"
    ] and
    // Exclude common false positives
    not model.getId() in ["self", "cls", "super", "dict", "list", "set", "str"] and
    // The model name should look like a model class (starts with uppercase)
    model.getId().regexpMatch("[A-Z][A-Za-z0-9_]*")
  )
}

/**
 * Check if we're in a service or repository class method
 */
predicate isInServiceOrRepository(Function f) {
  exists(Class c |
    c.getAMethod() = f and
    (c.getName().matches("%Service") or c.getName().matches("%Repository"))
  )
}

from Call call, Function func
where
  isORMQuery(call) and
  call.getScope() = func and
  not isInServiceOrRepository(func) and
  isUIOrAPIFile(call.getLocation().getFile())
select call, "Direct ORM access from UI/API layer. Use a service method instead to maintain separation of concerns."
