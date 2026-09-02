# Converts the Obsidian wikilinks used by this vault into normal site links.
require 'uri'

Jekyll::Hooks.register [:pages, :documents], :pre_render do |item|
  text = item.content
  text = text.gsub(/!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/) do
    file = Regexp.last_match(1)
    alt = Regexp.last_match(2) || File.basename(file, File.extname(file))
    image_path = file.split('/').map { |part| URI::DEFAULT_PARSER.escape(part) }.join('/')
    image_path = "Resources/#{image_path}" unless file.include?('/')
    "![#{alt}](/#{image_path})"
  end
  text = text.gsub(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/) do
    target = Regexp.last_match(1)
    label = Regexp.last_match(2) || target.split('#').last
    if target.start_with?('#')
      "[#{label}](##{Jekyll::Utils.slugify(target.delete_prefix('#'), mode: 'default')})"
    else
      path, fragment = target.split('#', 2)
      slug = Jekyll::Utils.slugify(path.sub(/\.md\z/i, ''), mode: 'pretty')
      href = "/#{slug}/"
      href += "##{Jekyll::Utils.slugify(fragment, mode: 'default')}" if fragment
      "[#{label}](#{href})"
    end
  end
  item.content = text
end
