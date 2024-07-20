from typing import Type, List
from PiFinder.ui.base import UIModule
from PiFinder.ui import menu_structure
from PiFinder.displays import DisplayBase


class MenuManager:
    def __init__(
        self,
        display_class: DisplayBase,
        camera_image,
        shared_state,
        command_queues,
        config_object,
        catalogs,
    ):
        self.display_class = display_class
        self.shared_state = shared_state
        self.ui_state = shared_state.ui_state()
        self.camera_image = camera_image
        self.command_queues = command_queues
        self.config_object = config_object
        self.catalogs = catalogs

        self.stack: List[Type[UIModule]] = []
        self.add_to_stack(menu_structure.pifinder_menu)

        self.marking_menu_active = False

    def remove_from_stack(self) -> None:
        if len(self.stack) > 1:
            self.stack.pop()

    def add_to_stack(self, item: dict) -> None:
        """
        Adds a new module to the stack by creating
        a new instance of the specified class, passing
        in all the required UI Module arguments + the
        item dict
        """
        if item.get("state") is not None:
            self.stack.append(item["state"])
        else:
            self.stack.append(
                item["class"](
                    display_class=self.display_class,
                    camera_image=self.camera_image,
                    shared_state=self.shared_state,
                    command_queues=self.command_queues,
                    config_object=self.config_object,
                    catalogs=self.catalogs,
                    item_definition=item,
                    add_to_stack=self.add_to_stack,
                    remove_from_stack=self.remove_from_stack,
                )
            )
            if item.get("stateful", False):
                item["state"] = self.stack[-1]

        self.stack[-1].active()  # type: ignore[call-arg]

    def message(self, message: str, timeout: float) -> None:
        self.stack[-1].message(message, timeout)  # type: ignore[arg-type]

    def screengrab(self) -> None:
        self.stack[-1].screengrab()  # type: ignore[call-arg]

    def update(self) -> None:
        if not self.marking_menu_active:
            self.stack[-1].update()  # type: ignore[call-arg]

    def key_number(self, number):
        self.stack[-1].key_number(number)

    def key_plus(self):
        self.stack[-1].key_plus()

    def key_minus(self):
        self.stack[-1].key_minus()

    def key_long_square(self):
        if not self.marking_menu_active:
            if self.stack[-1]._marking_menu_items is not None:
                self.marking_menu_active = True
        else:
            self.marking_menu_active = False

        if self.marking_menu_active:
            self.stack[-1].draw_marking_menu()

    def key_square(self):
        if self.marking_menu_active:
            self.marking_menu_active = False
            self.update()
        else:
            self.stack[-1].key_square()

    def key_long_up(self):
        pass

    def key_long_down(self):
        pass

    def key_long_right(self):
        pass

    def key_long_left(self):
        """
        Return to top of menu
        """
        self.stack = self.stack[:1]
        self.stack[0].active()

    def key_left(self):
        if self.marking_menu_active:
            self.marking_menu_active = False
            self.stack[-1].marking_menu_left()
            self.update()
        else:
            self.remove_from_stack()

    def key_up(self):
        if self.marking_menu_active:
            self.marking_menu_active = False
            self.stack[-1].marking_menu_up()
            self.update()
        else:
            self.stack[-1].key_up()

    def key_down(self):
        if self.marking_menu_active:
            self.marking_menu_active = False
            self.stack[-1].marking_menu_down()
            self.update()
        else:
            self.stack[-1].key_down()

    def key_right(self):
        if self.marking_menu_active:
            self.marking_menu_active = False
            self.stack[-1].marking_menu_right()
            self.update()
        else:
            self.stack[-1].key_right()
