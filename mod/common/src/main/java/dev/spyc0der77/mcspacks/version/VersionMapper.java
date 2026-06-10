package dev.spyc0der77.mcspacks.version;

import com.google.gson.Gson;
import com.google.gson.annotations.SerializedName;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

public final class VersionMapper {
    private final List<String> supported;
    private final Map<String, String> profiles;

    private VersionMapper(List<String> supported, Map<String, String> profiles) {
        this.supported = supported;
        this.profiles = profiles;
    }

    public static VersionMapper load() {
        try (InputStream stream = VersionMapper.class.getResourceAsStream("/mcs-versions.json")) {
            if (stream == null) {
                throw new IllegalStateException("Missing mcs-versions.json resource");
            }
            Index index = new Gson().fromJson(new InputStreamReader(stream, StandardCharsets.UTF_8), Index.class);
            if (index == null || index.supported == null || index.supported.isEmpty()) {
                throw new IllegalStateException("mcs-versions.json must define a non-empty supported version list");
            }
            if (index.profiles == null || index.profiles.isEmpty()) {
                throw new IllegalStateException("mcs-versions.json must define a non-empty profiles map");
            }
            return new VersionMapper(index.supported, index.profiles);
        } catch (Exception error) {
            throw new IllegalStateException("Failed to load MCS version index", error);
        }
    }

    public String resolveMcsProfile(String gameVersion, String configuredVersion) {
        String version = configuredVersion;
        if (version == null || version.isBlank() || "auto".equalsIgnoreCase(version)) {
            version = gameVersion;
        }
        if (profiles.containsKey(version)) {
            return profiles.get(version);
        }
        if (supported.contains(version)) {
            return version;
        }
        throw new IllegalStateException(
                "Minecraft version " + version + " is not supported by MCS. Supported: " + String.join(", ", supported)
        );
    }

    private static final class Index {
        @SerializedName("supported")
        private List<String> supported;

        @SerializedName("profiles")
        private Map<String, String> profiles;
    }
}
