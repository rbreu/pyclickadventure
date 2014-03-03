import pygame
from pygame.locals import QUIT, MOUSEBUTTONDOWN
import sys

FONTSIZE = 24

VIEW_LABEL = 'View'
TAKE_LABEL = 'Take'
MANIPULATE_LABEL = 'Manipulate'
ENTER_LABEL = 'Enter'
USE_ITEM_LABEL = 'Use item with...'
USE_ITEM_HELP_MESSAGE = 'Select an item from the screen.'
USE_ITEM_NOSUCCESS_MESSAGE = "I don't know how to do this."

screen = None
resolution = None
font = None
inventory = None


def init(resolution, caption, background_music=None, icon=None):
    pygame.init()
    globals()['screen'] = pygame.display.set_mode(resolution)
    pygame.display.set_caption(caption)
    globals()['font'] = pygame.font.SysFont(None, FONTSIZE)
    globals()['resolution'] = resolution
    globals()['inventory'] = Inventory()

    if background_music:
        pygame.mixer.init()
        pygame.mixer.music.load(background_music)
        pygame.mixer.music.set_endevent(pygame.constants.USEREVENT)
        pygame.mixer.music.play(loops=-1)

    if icon:
        icon = pygame.image.load(icon).convert_alpha()
        pygame.display.set_icon(icon)


class HoverMessageMixin:

    LABEL_PADDING = 3

    def draw_hover_message(self):
        txt = font.render(self.name, True, (0, 0, 0))
        mousepos = pygame.mouse.get_pos()
        x = mousepos[0]
        if mousepos[1] > resolution[1]/2:
            y = mousepos[1] - FONTSIZE
        else:
            y = mousepos[1] + FONTSIZE

        txt_rect = txt.get_rect()
        label = pygame.Surface((txt_rect.width + 2 * self.LABEL_PADDING,
                                txt_rect.height + 2 * self.LABEL_PADDING))
        label.set_alpha(200)
        label.fill((255,255,255))
        screen.blit(label,
                    (x - self.LABEL_PADDING, y - self.LABEL_PADDING))
        screen.blit(txt, (x, y))
        pygame.display.update()



class Item(pygame.sprite.Sprite, HoverMessageMixin):

    def __init__(self, image, topleft, name, description,
                 take_allow=True, take_attempt=None,
                 manipulate_allow=False, manipulate_attempt=None,
                 enter=None, use_item_callbacks=None):
        super(Item, self).__init__()
        self.name = name
        self.image = pygame.image.load(image).convert_alpha()
        self.original_image = self.image
        self.rect = self.image.get_rect()
        self.rect.topleft = topleft
        self.description = description
        self.take_allow = take_allow
        self.take_attempt = take_attempt
        self.manipulate_allow = manipulate_allow
        self.manipulate_attempt = manipulate_attempt
        self.enter = enter
        self.use_item_callbacks = use_item_callbacks or []

    def view_callback(self, room):
        room.status_message = self.description

    def enter_callback(self, room):
        room._switch_to_room = self.enter

    def use_item_callback(self, room):
        room.status_message = USE_ITEM_HELP_MESSAGE
        room._use_item = self

    def take_callback(self, room):
        if self.take_allow:
            room.remove(self)
            inventory.add_item(self)
            room._dirty = True
        elif self.take_attempt:
            room.status_message = self.take_attempt

    def manipulate_callback(self, room):
        if self.manipulate_allow:
            pass
        elif self.manipulate_attempt:
            room.status_message = self.manipulate_attempt

    def use_with(self, room, item):
        for it, callback in self.use_item_callbacks:
            if it == item:
                callback(room, self, item)
                return
        else:
            room.status_message = USE_ITEM_NOSUCCESS_MESSAGE

    def get_menu_entries(self, room):
        entries = []
        if self.description:
            entries.append((VIEW_LABEL, self.view_callback))
        if self.manipulate_allow or self.manipulate_attempt:
                entries.append((MANIPULATE_LABEL, self.manipulate_callback))
        if self in room:
            if self.take_allow or self.take_attempt:
                entries.append((TAKE_LABEL, self.take_callback))
            if self.enter is not None:
                entries.append((ENTER_LABEL, self.enter_callback))
        if self in inventory:
            entries.append((USE_ITEM_LABEL, self.use_item_callback))
        return entries

    def is_under_mouse(self):
        mousepos = pygame.mouse.get_pos()
        under = False
        if self.rect.collidepoint(mousepos):
            # Potential collision, check if pixel non-alpha:
            x = mousepos[0] - self.rect.topleft[0]
            y = mousepos[1] - self.rect.topleft[1]
            under = self.image.get_at((x, y))[3] != 0
        return under


class ItemMenu:

    PADDING = 3

    def __init__(self, item, room):
        self.item = item
        self.room = room
        self.txts = []
        self.width = 0
        for entry in self.item.get_menu_entries(self.room):
            txt = font.render(entry[0], True, (0, 0, 0))
            self.width = max(self.width, txt.get_rect().width)
            self.txts.append(txt)
        self.line_height = txt.get_rect().height
        self.x, self.y = pygame.mouse.get_pos()

        space_below = resolution[1] - (self.y + self.get_height())
        if space_below < 0:
            # menu too long to fit on screen; shift it
            self.y += space_below

    def get_height(self):
        return self.line_height * len(self.txts) + 2 * self.PADDING

    def draw(self):
        menu = pygame.Surface(
            (self.width + 2 * self.PADDING, self.get_height()))
        menu.set_alpha(200)
        menu.fill((255,255,255))
        screen.blit(menu, (self.x - self.PADDING, self.y - self.PADDING))
        y = self.y
        for txt in self.txts:
            screen.blit(txt, (self.x, y))
            y += self.line_height
        pygame.display.update()

    def get_entry_under_mouse(self):
        mousepos = pygame.mouse.get_pos()
        if mousepos[0] < self.x or mousepos[0] > self.x + self.width:
            return None

        y = mousepos[1] - self.PADDING - self.y
        entry = int(y / self.line_height)
        try:
            return self.item.get_menu_entries(self.room)[entry]
        except IndexError:
            return None


class Inventory(pygame.sprite.Group):

    PADDING = 5
    ITEM_SIZE = 50

    def get_x(self, pos):
        return pos * (self.ITEM_SIZE + self.PADDING) + self.PADDING

    def add_item(self, item):
        item.image = pygame.transform.smoothscale(
            item.image,
            (self.ITEM_SIZE, self.ITEM_SIZE))
        item.rect = item.image.get_rect()
        item.rect.topleft = (
            self.get_x(len(self)),
            resolution[1] - self.ITEM_SIZE - self.PADDING)
        self.add(item)

    def remove_item(self, item):
        self.remove(item)
        for i, item in enumerate(self):
            item.rect.topleft = (self.get_x(i), item.rect.topleft[1])

    def draw(self, *args, **kwargs):
        area = pygame.Surface((resolution[0],
                               self.ITEM_SIZE + 2 * self.PADDING))
        area.set_alpha(200)
        area.fill((255,255,255))
        screen.blit(area,
                    (0, resolution[1] - self.ITEM_SIZE - 2 * self.PADDING))

        super(Inventory, self).draw(*args, **kwargs)


class Arrow(HoverMessageMixin):

    def __init__(self, destination, name):
        self.name = name
        self.destination = destination

    def is_under_mouse(self):
        mousepos = pygame.mouse.get_pos()
        if self.arrow.collidepoint(mousepos):
            return True
        return False


class ArrowLeft(Arrow):

    def draw(self):
        self.arrow = pygame.draw.polygon(
            screen, (255, 255, 255),
            ((8, resolution[1]/2),
             (32, resolution[1]/2 - 24),
             (32, resolution[1]/2 + 24)))
        pygame.draw.polygon(
            screen, (0, 0, 0),
            ((10, resolution[1]/2),
             (30, resolution[1]/2 - 20),
             (30, resolution[1]/2 + 20)))


class ArrowRight(Arrow):

    def draw(self):
        arrow = pygame.draw.polygon(
            screen, (255, 255, 255),
            ((resolution[0] - 8, resolution[1]/2),
             (resolution[0] - 32, resolution[1]/2 - 24),
             (resolution[0] - 32, resolution[1]/2 + 24)))
        arrow = pygame.draw.polygon(
            screen, (0, 0, 0),
            ((resolution[0] - 10, resolution[1]/2),
             (resolution[0] - 30, resolution[1]/2 - 20),
             (resolution[0] - 30, resolution[1]/2 + 20)))


class Room(pygame.sprite.Group):

    def __init__(self, background, exit_left=None, exit_right=None):
        super(Room, self).__init__(self)
        self.background = pygame.image.load(background).convert()
        self.exit_left = exit_left
        self.exit_right = exit_right
        self.exits = []
        if exit_left:
            self.exits.append(ArrowLeft(destination=exit_left[0],
                                        name=exit_left[1]))
        if exit_right:
            self.exits.append(ArrowRight(destination=exit_left[0],
                                         name=exit_left[1]))

        self._dirty = True
        self._hover_item = None
        self._menu_item = None
        self.status_message = None
        self._switch_to_room = None
        self._use_item = None

    def draw_room(self):
        if self._dirty:
            screen.blit(self.background, (0, 0))
            self.draw(screen)
            self.draw_status_message()
            inventory.draw(screen)
            for arrow in self.exits:
                arrow.draw()
            pygame.display.update()
            self._dirty = False

    def draw_hover_message(self):
        if self._menu_item:
            return
        for item in list(self) + list(inventory) + self.exits:
            if item.is_under_mouse():
                if self._hover_item != item:
                    item.draw_hover_message()
                    self._hover_item = item
                return
        else:
            if self._hover_item is not None:
                self._dirty = True
            self._hover_item = None

    def clear_hover_message(self):
        if self._hover_item:
            self._dirty = True
            self.hover_item = None

    def draw_menu(self):
        for item in list(self) + list(inventory):
            if item.is_under_mouse() and item.get_menu_entries(self):
                self._menu_item = ItemMenu(item, self)
                self._menu_item.draw()
                return
        else:
            self._menu_item = None

    def handle_mouse_click(self):
        for arrow in self.exits:
            if arrow.is_under_mouse():
                self._switch_to_room = arrow.destination
                return

        self.clear_hover_message()
        self.clear_status_message()
        self.draw_room()
        if self._use_item is not None:
            for item in self:
                if item.is_under_mouse():
                    self._use_item.use_with(self, item)
                    self._use_item = None
                    self._dirty = True
                    return

        self._use_item = None
        if self._menu_item:
            entry = self._menu_item.get_entry_under_mouse()
            if entry:
                entry[1](self)
            self._menu_item = None
            self._dirty = True
        else:
            self.draw_menu()

    def handle_mouse_move(self):
        self.draw_hover_message()

    def draw_status_message(self):
        if not self.status_message:
            return

        PADDING = 10
        x = 0
        y = resolution[1]

        area = pygame.Surface((resolution[0], FONTSIZE + 2 * PADDING))
        area.set_alpha(200)
        area.fill((255,255,255))
        screen.blit(area, (0, 0))

        txt = font.render(self.status_message, True, (0, 0, 0))
        screen.blit(txt, (PADDING, PADDING))

        pygame.display.update()

    def clear_status_message(self):
        if self.status_message:
            self._dirty = True
            self.status_message = None


class MainLoop:

    def __init__(self, start_room):
        self.room = start_room
        self.clock = pygame.time.Clock()


    def run(self):

        self.room.draw_room()

        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == MOUSEBUTTONDOWN:
                    self.room.handle_mouse_click()

            self.room.handle_mouse_move()

            switch = self.room._switch_to_room
            if switch is not None:
                self.room._switch_to_room = None
                self.room = switch
                self.room._dirty = True
            self.room.draw_room()
            self.clock.tick(10)
