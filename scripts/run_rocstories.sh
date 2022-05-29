export TOKENIZERS_PARALLELISM=false

# model_name_or_path: roberta-large/roberta-base/cocolm-base/cocolm-large
CUDA_VISIBLE_DEVICES=0 python ../finetune/run_rocstories.py \
    --model_name_or_path roberta-large \
    --train_file ../data/rocstories/val_spring2016.csv \
    --test_file ../data/rocstories/test_spring2016.csv \
    --output_dir roc_model_dir \
    --do_train \
    --do_eval \
    --do_predict \
    --learning_rate 5e-6  \
    --num_train_epochs 40   \
    --save_steps 10000   \
    --evaluation_strategy "epoch" \
    --per_device_train_batch_size 32  \
    --per_device_eval_batch_size 32 \
    --overwrite_output