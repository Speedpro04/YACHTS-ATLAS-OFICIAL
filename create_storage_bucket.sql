-- Create a new storage bucket named 'media' for images, videos, and documents
insert into storage.buckets (id, name, public)
values (
  'media',
  'media',
  true
);

-- Allow public access to view files
create policy "Public Access to Media"
on storage.objects for select
to public
using ( bucket_id = 'media' );

-- Allow authenticated users to upload files
create policy "Authenticated users can upload media"
on storage.objects for insert
to authenticated
with check ( bucket_id = 'media' );

-- Allow authenticated users to update files
create policy "Authenticated users can update media"
on storage.objects for update
to authenticated
using ( bucket_id = 'media' );

-- Allow authenticated users to delete files
create policy "Authenticated users can delete media"
on storage.objects for delete
to authenticated
using ( bucket_id = 'media' );
