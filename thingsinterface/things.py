#!/usr/bin/env python

'''Python interface to Things.app's Applescript interface.

Lol! :'(
'''

import sys
import ScriptingBridge


# These integers are used to set the status of a task internally.
STATUS_MAP = {
    "open": 1952737647, #"tdio",
    "closed": 1952736109, #"tdcm",
    "cancelled": 1952736108 #"tdcl"
}


def getThings():
    return ScriptingBridge.SBApplication.applicationWithBundleIdentifier_(
        "com.culturedcode.ThingsMac")


class ThingsObject(object):
    def __init__(self):
        self.things = getThings()


class Projects(ThingsObject):
    """
    import ScriptingBridge
    import sys
    sys.path.append('../pythings3')
    from thingsinterface import ToDos, ToDo, Project, Projects
    getthings = ScriptingBridge.SBApplication.applicationWithBundleIdentifier_("com.culturedcode.ThingsMac")

    for k in getthings.projects():
    print(k.name())

    for proj in Projects():
        print("\"{}\" ({}) which is in {}".format(proj.name(), proj.id(), proj.area().id()))

    """
    def __init__(self):
        ThingsObject.__init__(self)
        self.projects = [Project(i) for i in self.things.projects()]

    def __len__(self):
        """Return the number of Project objects. """
        return len(self.projects)

    def __iter__(self):
        """Iterate over the Project objects."""
        for project in self.projects:
            yield project

    def __nonzero__(self):
        """Are there any Projects?"""
        if self.__len__() > 0:
            return True
        else:
            return False


class Project(object):

    @staticmethod
    def _getProjectByID(desired_id):
        things = getThings()
        return Project(project_obj=things.projects().objectWithID_(desired_id))

    def __init__(self, name="",
                 tags=[],
                 notes="",
                 project_object=None):
        ThingsObject.__init__(self)

        # self.__dict__ = {
        #     "name": project_object.name(),
        #     "notes": project_object.notes(),
        #     "creation_date": project_object.creationDate(),
        #     "modification_date": project_object.modificationDate(),
        #     "thingsid": project_object.id(),
        #     "todos": [ToDo.fromSBObject(i) for i in project_object.toDos()],
        #     "tags": project_object.tagNames().split(", "),
        #     "area": project_object.area().name(),
        #     "completion_date": project_object.completionDate(),
        #     # hack
        #     "completed": True if project_object.completionDate() else False,
        #     "contact": project_object.contact().name()
        # }

        if not project_object:  # create a new Project
            self.name = name
            self.project_object = self.things.classForScriptingClass_("project").alloc()
            self.project_object = self.project_object.initWithProperties_({
                "name": name,
                "tagNames": ", ".join(tags),
                "notes": notes,
            })
            things = getThings()
            things.toDos().append(self.project_object)

    def complete(self):
        #TODO
        # Implementation involves moving to List "Logbook"
        raise NotImplementedError


class ToDo(ThingsObject):

    @staticmethod
    def _getTodoByID(desired_id):
        things = getThings()
        return ToDo(todo_obj=things.toDos().objectWithID_(desired_id))

    def __init__(self, name="", tags=[], notes="", project="",
                 creation_date="", modification_date="",
                 location="Inbox", creation_area="", todo_obj=None):
        ThingsObject.__init__(self)

        if not todo_obj:  # create a new To-Do
            self.name = name
            if location and creation_area:
                sys.stderr.write(("WARNING! Inserting to a location and a creation_area at the "
                                  "same time will create two ToDos\n"))

            self.todo_object = self.things.classForScriptingClass_("to do").alloc()
            self.todo_object = self.todo_object.initWithProperties_({
                "name": name,
                "tagNames": ", ".join(tags),
                "notes": notes,
            })
            # print(self.todo_object)

            assigned = False
            for thingslist in self.things.lists():
                # print("list: {}".format(thingslist.name()))
                if thingslist.name() == location:
                    # print("a match, location/thingslist == {}/{}".format(location, thingslist.name()))
                    proj_assigned = False
                    for proj in self.things.projects():
                        if proj.name() == project:
                            # print("proj: {}".format(project))
                            if not todo_obj:
                                # print("ahoy!")
                                proj.toDos().append(self.todo_object)
                                proj_assigned = True
                        # else:
                            # if proj is not None:
                                # Project(proj)
            if not proj_assigned:  # Projects are more-specific than Areas. Therefore only put in an Area if not in a Project
                thingslist.toDos().append(self.todo_object)
                assigned = True
                # print("created a basic todo! well done you.")

            if not assigned:  # Projects are more-specific than Areas. Therefore only put in an Area if not in a Project
                for area in self.things.areas():
                    if area.name() == creation_area:
                        # print("area: {}".format(creation_area))
                        if not todo_obj:
                            area.toDos().append(self.todo_object)
            if not assigned and not proj_assigned:
                # In rare cases where there has been some kind of
                # weird internal OS X fuck-up, self.things.lists()
                # will be empty despite Things performing perfectly
                # fine and ToDos being accessed correctly. I have no
                # idea how to reproduce or guard against it, so
                # throwing an exception here is okay with me for now.
                raise KeyError(
                    ("Couldn't assign Things ToDo \"%s\" to a list "
                     "(location %s, available locations: %s.") % (
                         self.name, location, str(
                             [t.name() for t in self.things.lists()]))
                )
        else:
            self.name = todo_obj.name()
            self.todo_object = todo_obj

        self.tags = tags

        # print(self.project)
        # self.project = project
        # self.thingsid = self.todo_object.id()
        # self.creation_date = self.todo_object.creationDate()
        # self.modification_date = self.todo_object.modificationDate()

    @classmethod
    def fromSBObject(cls, todo_object):

        return cls(todo_object.name(), tags=todo_object.tagNames().split(", "),
                   notes=todo_object.name(), creation_area=todo_object.area().name(),
                   project=todo_object.project(),
                   creation_date=todo_object.creationDate(), modification_date=todo_object.modificationDate(),
                   todo_obj=todo_object)

    @staticmethod
    def _makeDictFromToDo(todo_object):
        """
import pprint
import sys
pp = pprint.PrettyPrinter(indent=4)
sys.path.append('../pythings3')
from thingsinterface import ToDos, ToDo, Project, Projects
for todo in ToDos('GitHub'):
    pp.pprint(todo._makeDictFromToDo(todo.todo_object))
        """
        return {
            "name": todo_object.name(),
            "notes": todo_object.notes(),
            "creation_date": todo_object.creationDate(),
            "modification_date": todo_object.modificationDate(),
            "thingsid": todo_object.id(),
            "tags": todo_object.tagNames().split(", "),
            "area": todo_object.area().name(),
            "area_id": todo_object.area().id(),  # THMAreaParentSource/uuid
            "project": todo_object.project(),
            "project_id": todo_object.project().id(),
            # "show": todo_object.show(),  # will bring application to the front
            "completion_date": todo_object.completionDate(),
            "completed": True if todo_object.completionDate() else False,
            "contact": todo_object.contact().name()
        }

    def cancel(self):
        self.todo_object.setStatus_(STATUS_MAP["cancelled"])

    def complete(self):
        self.todo_object.setStatus_(STATUS_MAP["closed"])

    def is_closed(self):
        return self.todo_object.status() == STATUS_MAP["closed"]

    def is_cancelled(self):
        return self.todo_object.status() == STATUS_MAP["cancelled"]

    def __cmp__(self, other):
        return self.thingsid == other.thingsid


class ToDos(ThingsObject):
    def __init__(self, thingslist=None):
        ThingsObject.__init__(self)
        selectedlist = None
        todos = []
        if thingslist:
            for templist in self.things.lists():
                if thingslist and templist.name() == thingslist:
                    selectedlist = templist
            if not selectedlist:
                # get ready to wait
                selectedlist = self.things
            todos = selectedlist.toDos()
        else:
            # get a random things object to have a type comparison
            todotype = self.things.toDos()[0]
            for thingsobj in self.things.toDos().get():
                if type(thingsobj) == type(todotype):
                    todos.append(thingsobj)

        todolist = []
        try:
            for todo in todos:
                tododata = ToDo.fromSBObject(todo)
                todolist.append(tododata)
        except IndexError as e:
            # If Things is in use while we're working on it the index
            # length can sometimes change. This will cause an
            # indexerror, just plough on regardless.
            todolist = []
            for todo in todos:
                tododata = ToDo.fromSBObject(todo)
                todolist.append(tododata)

        self.todos = todolist

    def __len__(self):
        """Return the number of todo objects. """
        return len(self.todos)

    def __iter__(self):
        """Iterate over the todo objects."""
        for todo in self.todos:
            yield todo

    def __nonzero__(self):
        """Are there any todos in this list?"""
        if self.__len__() > 0:
            return True
        else:
            return False


class Areas(ThingsObject):

    def __init__(self):
        ThingsObject.__init__(self)
        self.areas = [ Area(i) for i in self.things.areas() ]
        #x = Area(z)
        #print x.toDos

    def __len__(self):
        """Return the number of Area objects. """
        return len(self.areas)

    def __iter__(self):
        """Iterate over the Area objects."""
        for area in self.areas:
            yield area

    def __nonzero__(self):
        """Are there any Areas?"""
        if self.__len__() > 0:
            return True
        else:
            return False


class Area(object):
    def __init__(self, area_object):
        self.__dict__ = {
            "name": area_object.name(),
            "thingsid": area_object.id(),
            "todos": [ ToDo.fromSBObject(i) for i in area_object.toDos() ],
            "tags": area_object.tagNames().split(", "),
            # "suspended": True if area_object.suspended() else False
            }


class Contacts(ThingsObject):
    #TODO
    pass


class Contact(object):
    #TODO
    pass


def main():
    a = ToDo(name="Test", tags=["lol", "hax"],
             notes="definitely a test", location="Today") #, creation_area="Home")


if __name__ == "__main__":
    main()
