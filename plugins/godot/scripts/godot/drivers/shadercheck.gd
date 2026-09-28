# Compiles one shader under a real renderer and lets Godot print its own errors.
#
# Loading a .gdshader headless reports nothing even when the shader cannot
# compile (spec 3.5), because compilation happens in the rendering server and
# headless installs a dummy one. Assigning the shader to a material on a real
# ColorRect forces the compile, and SHADER ERROR lines reach stderr.
extends SceneTree

func _initialize() -> void:
	var shader_path := OS.get_environment("GODOT_MCP_SHADER")
	var shader := load(shader_path)
	if shader == null:
		printerr("GODOT_MCP_ERROR: could not load ", shader_path)
		quit(1)
		return

	var rect := ColorRect.new()
	rect.size = Vector2(64, 64)
	root.add_child(rect)

	var material := ShaderMaterial.new()
	material.shader = shader
	rect.material = material

	await process_frame
	await RenderingServer.frame_post_draw

	print("GODOT_MCP_OK")
	quit()
