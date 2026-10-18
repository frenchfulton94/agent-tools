[[kernel, required_threads_per_threadgroup(16, 16, 1)]]
void filterTile(texture2d<half, access::read>  src [[texture(0)]],
                texture2d<half, access::write> dst [[texture(1)]],
                uint2 gid [[thread_position_in_grid]])
{
    // dispatchThreads makes edge groups smaller, so this guard only protects
    // against a grid larger than the destination.
    if (gid.x >= dst.get_width() || gid.y >= dst.get_height()) return;
    dst.write(src.read(gid), gid);
}
