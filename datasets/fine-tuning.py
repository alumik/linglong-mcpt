import fire

from torch.utils.data import DataLoader

import linglong
import linglong.data.tfrecord


def main(
        dataset: str,
        input_path: str,
        output_path: str,
        model_config: str,
        split: str = 'train',
        dataset_config: str = 'configs/fine-tuning/local.yaml',
        vocab: str = '../common/vocab/char-13312.txt',
        pinyin_vocab: str | None = '../common/vocab/pinyin-1354.txt',
        use_cache: bool = False,
        items_per_file: int = 200000,
        special_tokens: dict[str, str] | None = None,
        n_examples: int = 3,
):
    with linglong.running('Loading configs') as spinner:
        special_tokens = {
            'start_token': '<|startoftext|>',
            'end_token': '<|endoftext|>',
            'part_separator': '<unused1>',
            'segment_separator': '<unused2>',
            **(special_tokens or {}),
        }
        model_config_path = model_config
        model_config = linglong.LingLongConfig.from_json_file(model_config_path)
        config = linglong.merge_configs({
            'dataset': dataset,
            'input_path': input_path,
            'output_path': output_path,
            'split': split,
            'vocab_path': vocab,
            'pinyin_vocab_path': pinyin_vocab,
            'special_tokens': special_tokens,
            'use_cache': use_cache,
            'items_per_file': items_per_file,
            'use_pinyin': model_config.use_pinyin,
            'n_positions': model_config.n_positions,
            'model_config_path': model_config_path,
            'dataset_config_path': dataset_config,
        }, linglong.load_config(dataset_config, key=dataset))
        spinner.write(linglong.prettify(config))

    with linglong.running(f'Processing {dataset} dataset', spinner=use_cache) as spinner:
        dataset = linglong.datasets.finetuning.load(config)
        meta_path, records_path = dataset.prepare()
        meta = linglong.load_config(meta_path)
        spinner.write(linglong.prettify({
            'meta_path': meta_path,
            'records_path': records_path,
            'meta': meta,
        }))

    print(linglong.text('Examples:', style=linglong.INFO))
    dataset = linglong.data.tfrecord.load_tfrecord_dataset(
        records_path,
        meta_path,
        use_pinyin=model_config.use_pinyin,
    )
    data_loader = DataLoader(dataset, batch_size=n_examples)
    tokenizer = linglong.get_tokenizers(vocab_path=vocab)[0]
    for batch in data_loader:
        linglong.data.print_model_inputs(batch, tokenizer=tokenizer)
        break


if __name__ == '__main__':
    linglong.init()
    fire.Fire(main)
