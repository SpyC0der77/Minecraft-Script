package dev.spyc0der.minecraftscript.forge;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.suggestion.SuggestionProvider;
import dev.spyc0der.minecraftscript.McsCommandResult;
import dev.spyc0der.minecraftscript.McsCommandService;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;

import java.util.function.Supplier;

public final class McsForgeCommands {
    private static final SuggestionProvider<CommandSourceStack> PACK_SUGGESTIONS = (context, builder) -> {
        for (String packName : McsCommandService.packNameSuggestions()) {
            builder.suggest(packName);
        }
        return builder.buildFuture();
    };

    private McsForgeCommands() {
    }

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("mcs")
                .requires(Commands.hasPermission(Commands.LEVEL_ADMINS))
                .then(Commands.literal("hotreloading")
                        .then(Commands.literal("enable")
                                .executes(ctx -> run(() -> McsCommandService.setHotReloading(true, null), ctx))
                                .then(Commands.argument("pack", StringArgumentType.string())
                                        .suggests(PACK_SUGGESTIONS)
                                        .executes(ctx -> run(
                                                () -> McsCommandService.setHotReloading(
                                                        true,
                                                        StringArgumentType.getString(ctx, "pack")
                                                ),
                                                ctx
                                        ))))
                        .then(Commands.literal("disable")
                                .executes(ctx -> run(() -> McsCommandService.setHotReloading(false, null), ctx))
                                .then(Commands.argument("pack", StringArgumentType.string())
                                        .suggests(PACK_SUGGESTIONS)
                                        .executes(ctx -> run(
                                                () -> McsCommandService.setHotReloading(
                                                        false,
                                                        StringArgumentType.getString(ctx, "pack")
                                                ),
                                                ctx
                                        )))))
                .then(Commands.literal("packs")
                        .then(Commands.literal("enable")
                                .executes(ctx -> run(() -> McsCommandService.setPackEnabled(null, true), ctx))
                                .then(Commands.argument("pack", StringArgumentType.string())
                                        .suggests(PACK_SUGGESTIONS)
                                        .executes(ctx -> run(
                                                () -> McsCommandService.setPackEnabled(
                                                        StringArgumentType.getString(ctx, "pack"),
                                                        true
                                                ),
                                                ctx
                                        ))))
                        .then(Commands.literal("disable")
                                .executes(ctx -> run(() -> McsCommandService.setPackEnabled(null, false), ctx))
                                .then(Commands.argument("pack", StringArgumentType.string())
                                        .suggests(PACK_SUGGESTIONS)
                                        .executes(ctx -> run(
                                                () -> McsCommandService.setPackEnabled(
                                                        StringArgumentType.getString(ctx, "pack"),
                                                        false
                                                ),
                                                ctx
                                        )))))
                .then(Commands.literal("reload")
                        .executes(ctx -> run(() -> McsCommandService.reload(null), ctx))
                        .then(Commands.argument("pack", StringArgumentType.string())
                                .suggests(PACK_SUGGESTIONS)
                                .executes(ctx -> run(
                                        () -> McsCommandService.reload(StringArgumentType.getString(ctx, "pack")),
                                        ctx
                                ))))
                .then(Commands.literal("create")
                        .then(Commands.argument("name", StringArgumentType.string())
                                .then(Commands.literal("global")
                                        .executes(ctx -> run(
                                                () -> McsCommandService.createPack(
                                                        StringArgumentType.getString(ctx, "name"),
                                                        "global"
                                                ),
                                                ctx
                                        )))
                                .then(Commands.literal("local")
                                        .executes(ctx -> run(
                                                () -> McsCommandService.createPack(
                                                        StringArgumentType.getString(ctx, "name"),
                                                        "local"
                                                ),
                                                ctx
                                        )))))
                .then(Commands.literal("list").executes(ctx -> run(McsCommandService::listPacks, ctx))));
    }

    private static int run(Supplier<McsCommandResult> action, CommandContext<CommandSourceStack> context) {
        McsCommandResult result = action.get().acknowledged(context.getInput());
        if (result.success()) {
            context.getSource().sendSuccess(() -> Component.literal(result.message()), true);
            return 1;
        }
        context.getSource().sendFailure(Component.literal(result.message()));
        return 0;
    }
}
