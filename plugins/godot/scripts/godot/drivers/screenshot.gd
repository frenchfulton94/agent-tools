# Runs as the MainLoop via `--script`, from OUTSIDE the project being captured.
# Nothing is written into the user's project: the scene path and the output path
# both arrive by environment variable, and the PNG is saved to an absolute path.
#
# Headless cannot do this -- the dummy renderer returns a null viewport texture
# (spec 3.2), so this driver must run windowed. The caller positions the window
# offscreen.
extends SceneTree

func _initialize() -> void:
	var scene_path := OS.get_environment("GODOT_MCP_SCENE")
	var out_path := OS.get_environment("GODOT_MCP_OUT")
	var frames := int(OS.get_environment("GODOT_MCP_FRAMES"))
	if frames <= 0:
		frames = 4

	var err := change_scene_to_file(scene_path)
	if err != OK:
		printerr("GODOT_MCP_ERROR: could not load scene ", scene_path)
		quit(1)
		return

	for _i in range(frames):
		await process_frame
	await RenderingServer.frame_post_draw

	var image := root.get_texture().get_image()
	if image == null:
		printerr("GODOT_MCP_ERROR: viewport texture was null (headless?)")
		quit(1)
		return

	var save_err := image.save_png(out_path)
	if save_err != OK:
		printerr("GODOT_MCP_ERROR: could not write ", out_path)
		quit(1)
		return

	# A blank/grey capture and a genuine one compress to nearly the same PNG
	# byte size, so file size alone cannot tell a caller the capture actually
	# saw the scene. Print the centre pixel so a caller (and this package's
	# own tests) can check content, not just that some PNG was written.
	var probe := image.get_pixel(image.get_size().x / 2, image.get_size().y / 2)
	print("GODOT_MCP_PIXEL ", probe.r8, ",", probe.g8, ",", probe.b8)

	print("GODOT_MCP_OK ", image.get_size().x, "x", image.get_size().y)
	quit()
