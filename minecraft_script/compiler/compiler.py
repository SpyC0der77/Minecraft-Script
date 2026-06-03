from .compile_interpreter import mcs_compile
from ..common import module_folder
from ..version_config import get_version_context, init_version_context, predefined_root, clear_version_context
from ..text_additions import text_error
from os import mkdir, listdir, rmdir
from time import time
from shutil import copyfile
import os

class Compiler:
    def __init__(self, ast: list, datapack_name: str, output_path: str, verbose: bool):
        self.ast = ast
        self.datapack_name = datapack_name
        self.datapack_id = datapack_name.lower().replace(' ', '_')
        self.output_path = output_path
        self.verbose = verbose
        self.root_folder = f"{self.output_path}/{self.datapack_name}"
        init_version_context(self.datapack_id)
        self.version = get_version_context()
        self.function_dir = self.version.function_dir
        self.function_tag_dir = self.version.function_tag_dir

    def function_path(self, *parts: str) -> str:
        return f"{self.root_folder}/data/{self.datapack_id}/{self.function_dir}/{'/'.join(parts)}"

    def make_scoreboard_event_init_commands(self, scoreboard_event_hooks):
        commands = []
        for hook in scoreboard_event_hooks:
            commands.extend((
                f'scoreboard objectives add {hook["scoreboard"]} {hook["criteria"]}',
                f'execute as @a run scoreboard players set @s {hook["scoreboard"]} 0',
            ))
        return commands

    def make_scoreboard_event_main_commands(self, scoreboard_event_hooks):
        commands = []
        for hook in scoreboard_event_hooks:
            commands.extend((
                (
                    f'execute as @a at @s if score @s {hook["scoreboard"]} matches 1.. run function '
                    f'{self.datapack_id}:user_functions/{hook["function_name"]}'
                ),
                f'execute as @a if score @s {hook["scoreboard"]} matches 1.. run scoreboard players set @s {hook["scoreboard"]} 0',
            ))
        return commands

    def make_scoreboard_event_kill_commands(self, scoreboard_event_hooks):
        commands = []
        for hook in scoreboard_event_hooks:
            commands.append(f'scoreboard objectives remove {hook["scoreboard"]}')
        return commands

    def make_init_file(self, scoreboard_event_hooks):
        text = (
            self.version.render("datapack.init.header")
            + "\n"
            + self.version.render("datapack.init")
            + "\n"
        )
        event_commands = self.make_scoreboard_event_init_commands(scoreboard_event_hooks)
        if event_commands:
            text += "\n" + "\n".join(event_commands) + "\n"
        with open(self.function_path("init.mcfunction"), 'xt') as init_file:
            init_file.write(text)

    def make_main_file(self, scoreboard_event_hooks):
        text = (
            self.version.render("datapack.main.header")
            + "\n"
            + self.version.render("datapack.main")
            + "\n"
        )
        event_commands = self.make_scoreboard_event_main_commands(scoreboard_event_hooks)
        if event_commands:
            text += "\n" + "\n".join(event_commands) + "\n"
        with open(self.function_path("main.mcfunction"), 'xt') as main_file:
            main_file.write(text)

    def make_kill_file(self, scoreboard_event_hooks):
        text = (
            self.version.render("datapack.kill.header")
            + "\n"
            + self.version.render("datapack.kill", datapackName=self.datapack_name)
            + "\n"
        )
        event_commands = self.make_scoreboard_event_kill_commands(scoreboard_event_hooks)
        if event_commands:
            event_text = "\n".join(event_commands)
            marker = "\ndatapack disable"
            if marker not in text:
                raise RuntimeError("Could not inject scoreboard event cleanup before datapack disable command")
            text = text.replace(marker, f"\n{event_text}\n{marker}", 1)
        with open(self.function_path("kill.mcfunction"), 'xt') as kill_file:
            kill_file.write(text)

    def make_click_item_check_file(self):
        check_text = self.version.render("click.check") + "\n"
        click_path = self.function_path(self.version.paths["clickable_items"])
        mkdir(click_path)
        with open(f'{click_path}/check.mcfunction', 'xt') as check_file:
            check_file.write(check_text)
        with open(f'{click_path}/run.mcfunction', 'xt') as run_file:
            run_file.write(self.version.render("click.run") + "\n")

    def import_math_files(self, used_math_ops):
        if not used_math_ops:
            return
        math_folder = self.function_path("math")
        mkdir(math_folder)
        source_folder = predefined_root("math")
        if not os.path.isdir(source_folder):
            print(text_error(f"No math templates for version {self.version.profile['minecraft_version']!r}"))
            exit(-1)
        for filename in listdir(source_folder):
            name = filename.split('.')[0]
            if name in used_math_ops:
                copyfile(
                    f'{source_folder}/{filename}',
                    f'{math_folder}/{filename}'
                )

    def import_builtins_files(self, used_builtins):
        if not used_builtins:
            return
        builtins_folder = self.function_path("builtins")
        mkdir(builtins_folder)
        source_folder = predefined_root("builtins")
        if not os.path.isdir(source_folder):
            print(text_error(f"No builtin templates for version {self.version.profile['minecraft_version']!r}"))
            exit(-1)
        for filename in listdir(source_folder):
            name = filename.split('.')[0]
            if name in used_builtins:
                copyfile(
                    f'{source_folder}/{filename}',
                    f'{builtins_folder}/{filename}'
                )

    def import_tags_folder(self):
        module_tags_folder = predefined_root("tags")
        if not os.path.isdir(module_tags_folder):
            print(text_error(f"No tag templates for version {self.version.profile['minecraft_version']!r}"))
            exit(-1)
        datapack_tags_folder = f'{self.root_folder}/data/{self.datapack_id}/tags'
        mkdir(datapack_tags_folder)
        for directory_name in listdir(module_tags_folder):
            current_module_folder = f'{module_tags_folder}/{directory_name}'
            current_datapack_folder = f'{datapack_tags_folder}/{directory_name}'
            mkdir(current_datapack_folder)
            for file_name in listdir(current_module_folder):
                copyfile(
                    f'{current_module_folder}/{file_name}',
                    f'{current_datapack_folder}/{file_name}'
                )

    def clean_empty_folder(self, folder_path):
        if os.path.exists(folder_path) and not os.listdir(folder_path):
            rmdir(folder_path)

    def generate_builtin_functions(self, used_math_ops, used_builtins, scoreboard_event_hooks):
        if self.verbose:
            print('\rBuilding built-in functions...', end="")
        self.make_init_file(scoreboard_event_hooks)
        if self.verbose:
            print('\rBuilding built-in functions... 17%', end="")
        self.make_main_file(scoreboard_event_hooks)
        if self.verbose:
            print('\rBuilding built-in functions... 33%', end="")
        self.make_kill_file(scoreboard_event_hooks)
        if self.verbose:
            print('\rBuilding built-in functions... 50%', end="")
        self.import_math_files(used_math_ops)
        self.clean_empty_folder(self.function_path("math"))
        if self.verbose:
            print('\rBuilding built-in functions... 67%', end="")
        self.import_builtins_files(used_builtins)
        self.clean_empty_folder(self.function_path("builtins"))
        if self.verbose:
            print('\rBuilding built-in functions... 83%', end="")
        self.make_click_item_check_file()
        if self.verbose:
            print('\rBuilding built-in functions... Done!')

    def clean_empty_code_blocks(self):
        code_blocks_folder = self.function_path("code_blocks")
        if os.path.exists(code_blocks_folder) and not os.listdir(code_blocks_folder):
            rmdir(code_blocks_folder)

    def build(self):
        start_time = time()
        if self.verbose:
            print(
                f'Building with name "{self.datapack_name}" (id: "{self.datapack_id}") '
                f'for Minecraft {self.version.profile["minecraft_version"]}'
            )
        try:
            mkdir(f"{self.root_folder}")
        except FileExistsError:
            print(text_error(f"Can't build file: {self.datapack_name !r} folder exists already!"))
            exit()
        mkdir(f'{self.root_folder}/data')
        if self.verbose:
            print('Creating default folders...', end=" ")
        mkdir(f'{self.root_folder}/data/minecraft')
        mkdir(f'{self.root_folder}/data/minecraft/tags')
        mkdir(f'{self.root_folder}/data/minecraft/tags/{self.function_tag_dir}')
        mkdir(f'{self.root_folder}/data/{self.datapack_id}')
        mkdir(self.function_path())
        mkdir(self.function_path("code_blocks"))
        mkdir(self.function_path("user_functions"))
        if self.verbose:
            print('Done!')
            print('Building Templates...', end=" ")
        with open(f'{self.root_folder}/pack.mcmeta', 'xt') as output_file:
            output_file.write(self.version.render_pack_mcmeta())
        copyfile(f'{module_folder}/compiler/build_templates/pack.png', f'{self.root_folder}/pack.png')
        tick_tag_path = (
            f'{self.root_folder}/data/minecraft/tags/{self.function_tag_dir}/'
            f'{self.version.function_tag_path("tick")}'
        )
        load_tag_path = (
            f'{self.root_folder}/data/minecraft/tags/{self.function_tag_dir}/'
            f'{self.version.function_tag_path("load")}'
        )
        with open(tick_tag_path, 'xt') as tick_file:
            tick_file.write(self.version.render_function_tag("tick"))
        with open(load_tag_path, 'xt') as load_file:
            load_file.write(self.version.render_function_tag("load"))
        if self.verbose:
            print("Done!")
        used_math_ops, used_builtins, scoreboard_event_hooks = mcs_compile(
            self.ast,
            f'{self.root_folder}/data/{self.datapack_id}/{self.function_dir}',
            self.datapack_id
        )
        self.generate_builtin_functions(used_math_ops, used_builtins, scoreboard_event_hooks)
        self.clean_empty_code_blocks()
        if self.verbose:
            print("Generating datapack tags...", end=" ")
        self.import_tags_folder()
        if self.verbose:
            print("Done!")
        elapsed_time = time() - start_time
        if self.verbose:
            print(f'Finished compiling {self.datapack_name}! Time Elapsed: {elapsed_time: 0.3f}s')
        clear_version_context()
